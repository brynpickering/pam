import pytest
from datetime import datetime, timedelta
from pam import activity

from pam.scoring import CharyparNagelPlanScorer
from pam.activity import Plan, Activity, Leg
from pam import utils
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY



testdata = [
    (timedelta(hours=1, minutes=0, seconds=0), 1),
    (timedelta(hours=1, minutes=30, seconds=0), 1.5),
    (timedelta(hours=1, minutes=0, seconds=30), 1 + 30/3600),
    (timedelta(hours=0, minutes=0, seconds=0), 0),
    (timedelta(hours=-1, minutes=0, seconds=0), -1),
]
@pytest.mark.parametrize("td,hours", testdata)
def test_timedelta_to_hours(td, hours):
    assert utils.timedelta_to_hours(td) == hours


testmtdata = [
    ("00:00:00", 0),
    ("01:00:00", 1),
    ("10:30:00", 10.5),
    ("00:00:01", 1/3600),
]
@pytest.mark.parametrize("mt,hours", testmtdata)
def test_matsim_duration_to_hours(mt, hours):
    assert utils.matsim_duration_to_hours(mt) == hours


activity_cnfg = {
        "performing": 6,
        "waiting": -0,
        "lateArrival": -18,
        "earlyDeparture": -10,
        "work": {
            "typicalDuration": "08:00:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
            "latestStartTime": "09:30:00",
            "earliestEndTime": "16:00:00",
            "minimalDuration": "05:00:00"
        },
        "home": {
            "typicalDuration": "12:00:00",
        },
        "shop": {
            "typicalDuration": "00:30:00",
            "openingTime": "06:00:00",
            "closingTime": "20:00:00",
        },
    }


def test_duration_score():
    activity = Activity(
        act = "work",
        start_time = mtdt(6*60),
        end_time = mtdt(14*60)
    )
    scorer = CharyparNagelPlanScorer()
    assert scorer.duration_score(activity, cnfg=activity_cnfg) == 48

    activity = Activity(
        act = "work",
        start_time = datetime(2005,2,2,6,0,0),
        end_time = datetime(2005,2,2,14,0,0)
    )
    assert scorer.duration_score(activity, cnfg=activity_cnfg) == 48

    activity = Activity(
        act = "work",
        start_time = datetime(2005,2,2,4,0,0),
        end_time = datetime(2005,2,2,14,0,0)
    )
    assert scorer.duration_score(activity, cnfg={
        "performing": 6,
        "work": {"openingTime": "06:00:00", "typicalDuration": "08:00:00"}
    }) == 48

    activity = Activity(
        act = "work",
        start_time = datetime(2005,2,2,13,0,0),
        end_time = datetime(2005,2,2,21,0,0)
    )
    assert scorer.duration_score(activity, cnfg={
        "performing": 6,
        "work": {"openingTime": "06:00:00", "typicalDuration": "08:00:00"}
    }) == 48

    activity = Activity(
        act = "work",
        start_time = datetime(2005,2,2,12,0,0),
        end_time = datetime(2005,2,2,21,0,0)
    )
    assert scorer.duration_score(activity, cnfg={
        "performing": 6,
        "work": {"openingTime": "06:00:00", "closingTime": "20:00:00", "typicalDuration": "08:00:00"}
    }) == 48


def test_negative_duration_score():
    scorer = CharyparNagelPlanScorer()
    activity = Activity(
        act = "work",
        start_time = mtdt(14*60),
        end_time = mtdt(16*60)
    )
    assert int(scorer.duration_score(activity, cnfg=activity_cnfg)) == -16

    activity = Activity(
        act = "work",
        start_time = mtdt(15*60),
        end_time = mtdt(14*60)
    )
    assert int(scorer.duration_score(activity, cnfg=activity_cnfg)) == -69

    activity = Activity(
        act = "work",
        start_time = mtdt(16*60),
        end_time = mtdt(14*60)
    )
    assert int(scorer.duration_score(activity, cnfg=activity_cnfg)) == -87

def test_waiting_score():
    activity = Activity(
        act = "work",
        start_time = mtdt(4*60),
        end_time = mtdt(14*60)
    )
    scorer = CharyparNagelPlanScorer()
    assert scorer.waiting_score(activity, cnfg=activity_cnfg) == 0

    assert scorer.waiting_score(activity, cnfg={
        "waiting": -1,
        "work": {"openingTime": "06:00:00"}
    }) == -2

    activity = Activity(
        act = "work",
        start_time = mtdt(6*60)
    )
    assert scorer.waiting_score(activity, cnfg=activity_cnfg) == 0

    activity = Activity(
        act = "work",
        start_time = mtdt(7*60)
    )
    assert scorer.waiting_score(activity, cnfg=activity_cnfg) == 0


def test_late_arrival_score():
    activity = Activity(
        act = "work",
        start_time = mtdt(6*60),
        end_time = mtdt(14*60)
    )
    scorer = CharyparNagelPlanScorer()
    assert scorer.late_arrival_score(activity, cnfg=activity_cnfg) == 0

    activity = Activity(
        act = "work",
        start_time = mtdt(10*60 + 30),
        end_time = mtdt(18*60 + 30)
    )
    assert scorer.late_arrival_score(activity, cnfg=activity_cnfg) == -18

    activity = Activity(
        act = "work",
        start_time = datetime(2020,1,1,10,30,0),
        end_time = datetime(2020,1,1,18,30,0)
    )
    assert scorer.late_arrival_score(activity, cnfg=activity_cnfg) == -18


def test_early_departure_score():
    activity = Activity(
        act = "work",
        start_time = mtdt(6*60),
        end_time = mtdt(16*60)
    )
    scorer = CharyparNagelPlanScorer()
    assert scorer.early_departure_score(activity, cnfg=activity_cnfg) == 0

    activity = Activity(
        act = "work",
        start_time = mtdt(7*60),
        end_time = mtdt(15*60)
    )
    assert scorer.early_departure_score(activity, cnfg=activity_cnfg) == -10

    activity = Activity(
        act = "work",
        start_time = datetime(2020,1,1,10,30,0),
        end_time = datetime(1920,1,1,15,0,0)
    )
    assert scorer.early_departure_score(activity, cnfg=activity_cnfg) == -10


def test_too_short_score():
    activity = Activity(
        act = "work",
        start_time = mtdt(6*60),
        end_time = mtdt(16*60)
    )
    scorer = CharyparNagelPlanScorer()
    assert scorer.too_short_score(activity, cnfg=activity_cnfg) == 0

    activity = Activity(
        act = "work",
        start_time = mtdt(7*60),
        end_time = mtdt(11*60)
    )
    assert scorer.too_short_score(activity, cnfg=activity_cnfg) == -10


leg_cnfg = {
        "mUM": 10,
        "utilityOfLineSwitch": -1,
        "car": {
            "constant": -10,
            "dailyMonetaryConstant": -1,
            "dailyUtilityConstant": -1,
            "marginalUtilityOfDistance": -0.001,
            "marginalUtilityOfTravelling": -10,
            "monetaryDistanceRate": -0.0001
        }
    }

def test_mode_constant_score():
    scorer = CharyparNagelPlanScorer()
    leg = Leg(
        mode='car'
    )
    assert scorer.mode_constant_score(leg, cnfg=leg_cnfg) == -10

def test_travel_time_score():
    scorer = CharyparNagelPlanScorer()
    leg = Leg(
        mode='car',
        start_time=mtdt(0),
        end_time=mtdt(60)
    )
    assert scorer.travel_time_score(leg, cnfg=leg_cnfg) == -10


def test_travel_distamce_score():
    scorer = CharyparNagelPlanScorer()
    leg = Leg(
        mode='car',
        start_time=mtdt(0),
        end_time=mtdt(60),
        distance=1000
    )
    assert scorer.travel_distance_score(leg, cnfg=leg_cnfg) == -2


def test_wrapper():
    scorer = CharyparNagelPlanScorer()
    activities = [
        Activity(act='home', start_time=mtdt(0), end_time=mtdt(420)),
        Activity(act='shop', start_time=mtdt(480), end_time=mtdt(510)),
        Activity(act='work', start_time=mtdt(540), end_time=mtdt(1200)),
        Activity(act='home', start_time=mtdt(1260), end_time=END_OF_DAY)
    ]
    wrapped, other = scorer.activities_wrapper(activities)
    assert isinstance(wrapped, Activity)
    assert isinstance(other, list)
    assert len(other) == 2
    assert wrapped.act == 'home'
    assert wrapped.start_time == mtdt(1260)
    assert wrapped.end_time == mtdt(420) + timedelta(days=1)
    assert wrapped.duration.seconds == 36000


def test_score_plan_activities():
    plan = Plan()
    plan.day = [
        Activity(act='home', start_time=mtdt(0), end_time=mtdt(420)),
        Leg(mode='car', start_time=mtdt(420), end_time=mtdt(480)),
        Activity(act='shop', start_time=mtdt(480), end_time=mtdt(510)),
        Leg(mode='car', start_time=mtdt(510), end_time=mtdt(540)),
        Activity(act='work', start_time=mtdt(540), end_time=mtdt(1020)),
        Leg(mode='car', start_time=mtdt(1020), end_time=mtdt(1140)),
        Activity(act='home', start_time=mtdt(1140), end_time=END_OF_DAY)
    ]
    scorer = CharyparNagelPlanScorer()
    assert scorer.score_plan_activities(plan, cnfg=activity_cnfg) == 123


full_config = {
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

def test_score_plan_legs():
    plan = Plan()
    plan.day = [
        Activity(act='home', start_time=mtdt(0), end_time=mtdt(420)),
        Leg(mode='car', start_time=mtdt(420), end_time=mtdt(480), distance=1000),
        Activity(act='shop', start_time=mtdt(480), end_time=mtdt(510)),
        Leg(mode='walk', start_time=mtdt(510), end_time=mtdt(540), distance=1000),
        Activity(act='work', start_time=mtdt(540), end_time=mtdt(1020)),
        Leg(mode='car', start_time=mtdt(1020), end_time=mtdt(1140), distance=1000),
        Activity(act='home', start_time=mtdt(1140), end_time=END_OF_DAY)
    ]
    scorer = CharyparNagelPlanScorer()
    assert scorer.score_plan_legs(plan, cnfg=full_config) == -47 


def test_score_plan():
    plan = Plan()
    plan.day = [
        Activity(act='home', start_time=mtdt(0), end_time=mtdt(420)),
        Leg(mode='car', start_time=mtdt(420), end_time=mtdt(480), distance=1000),
        Activity(act='shop', start_time=mtdt(480), end_time=mtdt(510)),
        Leg(mode='walk', start_time=mtdt(510), end_time=mtdt(540), distance=1000),
        Activity(act='work', start_time=mtdt(540), end_time=mtdt(1020)),
        Leg(mode='car', start_time=mtdt(1020), end_time=mtdt(1140), distance=1000),
        Activity(act='home', start_time=mtdt(1140), end_time=END_OF_DAY)
    ]
    scorer = CharyparNagelPlanScorer()
    assert scorer.score(plan, cnfg=full_config) == 65 
