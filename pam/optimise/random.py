from datetime import timedelta
from numpy import random
from copy import deepcopy
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#import seaborn as sns
import plotly.express as px

from pam.activity import Plan, Leg, Activity
from pam.plot import plans
from pam.variables import END_OF_DAY
from pam.scoring import CharyparNagelPlanScorer


def reschedule(
    plan: Plan,
    plans_scorer = CharyparNagelPlanScorer,
    config : dict = {},
    horizon : int = 5,
    sensitivity : float = 0.01,
    patience : int = 1000
    ):
    best_score = plans_scorer.score_plan(plan, config)
    print(f"Initial best score at iteration 0: {best_score}")
    best_scores = {0:best_score}
    stopper = Stopper(horizon=horizon ,sensitivity=sensitivity)
    data = {
        "iteration": [],
        "d0": [],
        "d1": [],
        "d2": [],
        "score": [],
    }
    for n in range(patience):
        proposed_plan = random_mutate_activity_durations(plan, copy=True)
        score = plans_scorer.score_plan(proposed_plan, config)
        data["iteration"].append(n + 1)
        data["d0"].append(d0(proposed_plan))
        data["d1"].append(d1(proposed_plan))
        data["d2"].append(d2(proposed_plan))
        data["score"].append(score)
        if score > best_score:
            print(f"New best score at iteration {n}: {score}")
            best_scores[n] = score
            best_score = score
            plan = proposed_plan
            if not stopper.ok(score):
                return plan, best_scores
    df = pd.DataFrame(data)
    print(df)
    plot_scoring_sequence_2d(data["d0"], data["d1"], data["d2"], data["score"], 'viridis')
    plot_scoring_sequence_3d(df, "d0", "d1", "d2", "score")
    return plan, best_scores


def random_mutate_activity_durations(plan: Plan, copy=True):
    allowance = 24*60*60  # seconds
    for leg in plan.legs:
        allowance -= leg.duration.total_seconds()
    n_activities = len(list(plan.activities))
    activity_durations = [timedelta(seconds=int(random.random() * allowance / n_activities)) for n in range(n_activities)]
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


def d0(plan):
    d0 = plans.build_plan_df(plan)["dur"].iloc[0]
    return d0

def d1(plan):
    d1 = plans.build_plan_df(plan)["dur"].iloc[2]
    return d1

def d2(plan):
    d2 = plans.build_plan_df(plan)["dur"].iloc[4]
    return d2

def plot_scoring_sequence_2d(x, y, z, colour, cmap):
    fig = plt.figure(figsize=(13, 10))
    plt.scatter(x, y, c=colour, cmap=cmap, alpha=0.5)
    plt.plot(np.linspace(0,24,100), 24-(np.linspace(0,24,100)))
    plt.xlim([0, 25])
    plt.ylim([0, 25])
    plt.xlabel("d0")
    plt.ylabel("d1")
    plt.colorbar(label='Charypar Nagel Score')
    #plt.contour([x,y], z, colors='black', alpha=0.4)
    plt.show()

def plot_scoring_sequence_3d(df, x, y, z, colour):
    fig = px.scatter_3d(df, x=x, y=y, z=z, color=colour)
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, 25]),
            yaxis=dict(range=[0, 25]),
            zaxis=dict(range=[0, 25])),
        width=700,
        margin=dict(r=20, l=10, b=10, t=10)
    )
    fig.show()


class Stopper():
    def __init__(self, horizon=5, sensitivity=0.01) -> None:
        self.record = []
        self.horizon = horizon
        self.sensitivity=sensitivity

    def ok(self, score):
        self.record.append(score)
        if len(self.record) > self.horizon:
            self.record.pop(0)
            if self.record[-1] - self.record[0] < self.sensitivity:
                print("Stopping early")
                return False
        return True