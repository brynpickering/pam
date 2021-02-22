from datetime import timedelta
from numpy import random
from copy import deepcopy
from datetime import timedelta

from pam.activity import Plan, Leg, Activity
from pam.variables import END_OF_DAY


def random_mutate_activity_durations(plan: Plan, copy=True):
    allowance = 24*60*60  # seconds
    for leg in plan.legs:
        allowance -= leg.duration.total_seconds()
    n_activities = len(list(plan.activities))
    activity_durations = [timedelta(seconds=int(random.random() * allowance / n_activities)) for n in range(n_activities)]
    print(activity_durations)
    if copy:
        plan = deepcopy(plan)
    time = plan.day[0].shift_duration(new_duration=activity_durations.pop(0))
    idx = 1
    for activity_duration, leg_duration in zip(activity_durations, [leg.duration for leg in plan.legs]):
        time = plan.day[idx].shift_duration(new_start_time=time, new_duration=leg_duration)
        time = plan.day[idx+1].shift_duration(new_start_time=time, new_duration=activity_duration)
        idx += 2
    plan.day[-1].end_time = END_OF_DAY
    return plan
