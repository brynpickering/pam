from pam.activity import Plan, Activity, Leg
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY
from pam import optimise


def test_random_mutate_activity_durations():
    plan = Plan()
    plan.day = [
        Activity(act='home', area=1, start_time=mtdt(0), end_time=mtdt(420)),
        Leg(mode='car', start_area=1, end_area=2, start_time=mtdt(420), end_time=mtdt(480), distance=1000),
        Activity(act='shop', area=2, start_time=mtdt(480), end_time=mtdt(510)),
        Leg(mode='walk', start_area=2, end_area=3, start_time=mtdt(510), end_time=mtdt(540), distance=1000),
        Activity(act='work', area=3, start_time=mtdt(540), end_time=mtdt(1020)),
        Leg(mode='car', start_area=3, end_area=1, start_time=mtdt(1020), end_time=mtdt(1140), distance=1000),
        Activity(act='home', area=1, start_time=mtdt(1140), end_time=END_OF_DAY)
    ]
    new = optimise.random_mutate_activity_durations(plan, copy=True)
    assert new.is_valid


def test_random_mutate_activity_durations_overwrite():
    plan = Plan()
    plan.day = [
        Activity(act='home', area=1, start_time=mtdt(0), end_time=mtdt(420)),
        Leg(mode='car', start_area=1, end_area=2, start_time=mtdt(420), end_time=mtdt(480), distance=1000),
        Activity(act='shop', area=2, start_time=mtdt(480), end_time=mtdt(510)),
        Leg(mode='walk', start_area=2, end_area=3, start_time=mtdt(510), end_time=mtdt(540), distance=1000),
        Activity(act='work', area=3, start_time=mtdt(540), end_time=mtdt(1020)),
        Leg(mode='car', start_area=3, end_area=1, start_time=mtdt(1020), end_time=mtdt(1140), distance=1000),
        Activity(act='home', area=1, start_time=mtdt(1140), end_time=END_OF_DAY)
    ]
    new = optimise.random_mutate_activity_durations(plan, copy=False)
    assert new.is_valid
    assert new == plan


def test_random_mutate_activity_durations_stay_at_home():
    plan = Plan()
    plan.day = [
        Activity(act='home', area=1, start_time=mtdt(0), end_time=END_OF_DAY),
    ]
    new = optimise.random_mutate_activity_durations(plan, copy=True)
    assert new.is_valid