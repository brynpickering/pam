from datetime import timedelta
from numpy import random
from copy import deepcopy
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
        "score": [],
    }
    for n in range(patience):
        proposed_plan = random_mutate_activity_durations(plan, copy=True)
        score = plans_scorer.score_plan(proposed_plan, config)
        duration = duration_variables(proposed_plan)
        data["iteration"].append(n + 1)
        data["d0"].append(duration[0])
        data["d1"].append(duration[1])
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
    plot_scoring_sequence_2d(data["d0"], data["d1"], data["score"], data["score"], 'viridis')
    plot_scoring_sequence_3d(df, "d0", "d1", "score", "score")
    #plot_scoring_sequence_3d(data["d0"], data["d1"], data["score"], data["score"] )
    return plan, best_scores


def random_mutate_activity_durations(plan: Plan, copy=True):
    allowance = 24*60*60  # seconds
    for leg in plan.legs:
        allowance -= leg.duration.total_seconds()
    n_activities = len(list(plan.activities))
    random_list = [random.random() for n in range(n_activities)]
    random_list = [r / sum(random_list) for r in random_list]
    activity_durations = [timedelta(seconds=int(r * allowance)) for r in random_list]
    #activity_durations = [timedelta(seconds=int(random.random() * allowance)) for n in range(n_activities)]
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


def duration_variables(Plan):
    duration_variables = []
    for activity in Plan.activities:
        duration = (activity.duration.total_seconds())/3600
        duration_variables.append(duration)
    return duration_variables


def plot_scoring_sequence_2d(x, y, z, colour, cmap):
    fig = plt.figure(figsize=(13, 10))
    plt.scatter(x, y, c=colour, cmap=cmap, alpha=0.5)
    plt.plot(np.linspace(0,24,100), 24-(np.linspace(0,24,100)))
    plt.xlim([0, 25])
    plt.ylim([0, 25])
    plt.xlabel("d0")
    plt.ylabel("d1")
    plt.colorbar(label='Charypar Nagel Score')
    #plt.contour(x, y, z, colors='black', alpha=0.4)
    plt.show()

def plot_scoring_sequence_3d(df, x, y, z, colour):
    fig = px.scatter_3d(df, x=x, y=y, z=z, color=colour)
    # fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)]) #z needs to be a list of lists (matrix) for this to work
    # fig.update_traces(contours_z=dict(show=True, usecolormap=True,
    #                                   highlightcolor="limegreen", project_z=True))
    # fig.update_layout(title='Random Search Parameter Space', autosize=True)
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, 25]),
            yaxis=dict(range=[0, 25]),
            zaxis=dict(range=[0, max(z)])),
        width=700,
        margin=dict(r=20, l=10, b=10, t=10)
    )
    fig.show()

def contour_plot(
    plan: Plan,
    plans_scorer = CharyparNagelPlanScorer,
    config : dict = {},
    copy=True
    ):
    allowance = 24*60*60  # seconds
    leg_durations = []
    for leg in plan.legs:
        allowance -= leg.duration.total_seconds()
        leg_durations.append(leg.duration.total_seconds())
    dur_0 = list(range(0, 25, 1))
    dur_1 = list(range(0, 25, 1))
    z = np.empty([len(dur_0), len(dur_1)])
    for d0 in dur_0:
        for d1 in dur_1:
            total_time = (d0+d1)*3600
            if total_time <= allowance:
                d2 = allowance - total_time
                if copy:
                    plan = deepcopy(plan)
                time = plan.day[0].shift_duration(new_duration=timedelta(seconds=int(d0*3600)))
                time = plan.day[1].shift_duration(new_start_time=time, new_duration=timedelta(seconds=int(leg_durations[0])))
                time = plan.day[2].shift_duration(new_start_time=time, new_duration=timedelta(seconds=int(d1*3600)))
                time = plan.day[3].shift_duration(new_start_time=time, new_duration=timedelta(seconds=int(leg_durations[1])))
                plan.day[4].shift_duration(new_start_time=time, new_duration=timedelta(seconds=int(d2)))
                #plan.day[-1].end_time = END_OF_DAY
                score = plans_scorer.score_plan(plan, config)
                z[d0][d1] = score

    #Plot - Style 1
    fig1 = go.Figure(data=[go.Surface(z=z, x=dur_0, y=dur_1)])
    fig1.update_traces(contours_z=dict(show=True,
                                      usecolormap=True,
                                      highlightcolor="limegreen",
                                      project_z=True))
    fig1.update_layout(title='Contour Plot Style 1 - Random Search Parameter Space', autosize=False,
                  scene_camera_eye=dict(x=1.87, y=0.88, z=-0.64),
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90)
    )

    #Plot - Style 2
    fig2 = go.Figure(data=go.Contour(z=z, x=dur_0, y=dur_1))
    fig2.update_layout(title='Contour Plot Style 2 - Random Search Parameter Space', autosize=True)

    fig1.show()
    fig2.show()


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