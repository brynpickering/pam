from typing import DefaultDict, Optional
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
import logging

from pam.activity import Activity, Leg, Plan
from pam import utils


class CharyparNagelPlanScorer:

    example_config = {
        "mUM": 10,
        "utilityOfLineSwitch": -1,
        "performing": 6,
        "waiting": -0,
        "lateArrival": -18,
        "earlyDeparture": -10,
        "work": {
            "typicalDuration": "08:00:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
            "latestStartTime": "09:30:00",
            "earliestEndTime": "16:00:00"
        },
        "home": {
            "typicalDuration": "12:00:00",
        },
        "shop": {
            "typicalDuration": "00:30:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
        },
        "car": {
            "constant": -10,
            "dailyMonetaryConstant": -1,
            "dailyUtilityConstant": -1,
            "marginalUtilityOfDistance": -0.001,
            "marginalUtilityOfTravelling": -1,
            "monetaryDistanceRate": -0.0001
        },
        "walk": {
            "constant": -20,
        }
    }

    def __init__(self) -> None:
        """
        Charypar-Nagel plan scorer.
        """
        self.logger = logging.getLogger(__name__)

    def score(
        self,
        plan: Plan,
        cnfg: dict,
        plan_cost: Optional[float] = None
        ) -> float:
        """
        Score a pam.activity.Plan

        Args:
            plan (pam.activity.Plan): activity plan to be scored.
            cnfg (dict): configuration for plan scoring, refer to self.example_config for example.
            plan_cost (float, optional): Optionally add a plan monetary cost. Defaults to None.

        Returns:
            float: Charypar-Nagel score
        """
        return self.score_plan_activities(plan, cnfg) \
            + self.score_plan_legs(plan, cnfg) \
            + self.plan_monetary_cost_score(plan_cost, cnfg) \
            + self.plan_daily_score(plan, cnfg)
    
    def plan_monetary_cost_score(self, plan_cost, cnfg) -> float:
        if plan_cost is not None:
            return cnfg.get("mUM", 1) * plan_cost
        return 0.0
    
    def plan_daily_score(self, plan, cnfg) -> float:
        modes = plan.mode_classes
        return sum([self.mode_daily_score(mode, cnfg) for mode in modes])

    def mode_daily_score(self, mode, cnfg) -> float:
        return cnfg[mode].get("dailyUtilityConstant", 0) \
            + (cnfg[mode].get("dailyMonetaryConstant", 0) * cnfg.get("mUM", 1))

    def score_plan_activities(self, plan, cnfg):
        activities = list(plan.activities)
        if len(activities) == 1:
            return self.score_activity(activities[0], cnfg)
        wrapped, other = self.activities_wrapper(activities)
        return self.score_activity(wrapped, cnfg) \
            + sum([self.score_activity(act, cnfg) for act in other])

    def activities_wrapper(self, activities):
        non_wrapped = activities[1:-1]
        if activities[0].act == activities[-1].act:
            self.logger.warning(
                f"Wrapping non-alike activities: {activities[0].act} -> {activities[-1].act}"
                )

        wrapped_act = Activity(
            act=activities[0].act,
            start_time=activities[-1].start_time,
            end_time=activities[0].end_time + td(days=1)
        )
        return wrapped_act, non_wrapped

    def score_activity(self, activity, cnfg):
        return sum([
            self.duration_score(activity, cnfg),
            self.waiting_score(activity, cnfg),
            self.late_arrival_score(activity, cnfg),
            self.early_departure_score(activity, cnfg)
        ])

    def score_plan_legs(self, plan, cnfg):
        return sum([self.score_leg(leg, cnfg) for leg in plan.legs])

    def score_leg(self, leg, cnfg):
        return sum([
            self.mode_constant_score(leg, cnfg),
            self.travel_time_score(leg, cnfg),
            self.travel_distance_score(leg, cnfg)
        ])

    def duration_score(self, activity, cnfg) -> float:
        prio = 1
        performing = cnfg["performing"]
        typical_dur = utils.matsim_duration_to_hours(cnfg[activity.act]["typicalDuration"])

        opening_time = cnfg[activity.act].get("openingTime")
        if opening_time is not None:
            opening_time = utils.matsim_time_to_datetime(opening_time)
            if opening_time.time() > activity.start_time.time():
                duration = (activity.end_time - opening_time).seconds / 3600
            else:
                duration = activity.hours
        else:
            duration = activity.hours
        
        closing_time = cnfg[activity.act].get("closingTime")
        if closing_time is not None:
            closing_time = utils.matsim_time_to_datetime(closing_time)
            if closing_time.time() < activity.end_time.time():
                duration -= (activity.end_time - closing_time).seconds / 3600

        if duration < typical_dur / np.e:
            return (duration - typical_dur/np.e) * performing * (typical_dur / np.e)

        return performing * typical_dur * (np.log(duration / typical_dur) + (1 / prio))

    def waiting_score(self, activity, cnfg) -> float:
        waiting = cnfg["waiting"]
        if not waiting:
            return 0.0
        opening_time = cnfg[activity.act].get("openingTime")
        if opening_time is None:
            return 0.0
        opening_dt = utils.matsim_time_to_datetime(opening_time)
        start_dt = activity.start_time
        if start_dt.time() < opening_dt.time():
            return waiting * (opening_dt - start_dt).seconds / 3600
        return 0.0

    def late_arrival_score(self, activity, cnfg) -> float:
        if cnfg[activity.act].get("latestStartTime") is not None \
        and cnfg.get("lateArrival"):
            latest_start_time = utils.matsim_time_to_datetime(
                cnfg[activity.act]["latestStartTime"]
                )
            if activity.start_time.time() > latest_start_time.time():
                return cnfg["lateArrival"] \
                    * (activity.start_time - latest_start_time).seconds / 3600
        return 0.0

    def early_departure_score(self, activity, cnfg) -> float:
        if cnfg[activity.act].get("earliestEndTime") is not None \
        and cnfg.get("earlyDeparture"):
            earliest_end_time = utils.matsim_time_to_datetime(
                cnfg[activity.act]["earliestEndTime"]
                )
            if activity.end_time.time() < earliest_end_time.time():
                return cnfg["earlyDeparture"] \
                    * (earliest_end_time - activity.end_time).seconds / 3600
        return 0.0

    def too_short_score(self, activity, cnfg) -> float:
        raise NotImplementedError

    def mode_constant_score(self, leg, cnfg):
        return cnfg[leg.mode].get("constant", 0.0)

    def travel_time_score(self, leg, cnfg) -> float:
        return leg.hours * cnfg[leg.mode].get("marginalUtilityOfTravelling", 0.0)
    
    def travel_distance_score(self, leg, cnfg) -> float:
        return leg.distance * (cnfg[leg.mode].get("marginalUtilityOfDistance", 0.0) \
             + (cnfg.get("mUM", 1.0) * cnfg[leg.mode].get("monetaryDistanceRate", 0.0)))