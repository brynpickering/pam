import pytest
import random
import pandas as pd
import geopandas as gp
from shapely.geometry import Point, Polygon

from pam.samplers import tour


def test_frequency_sampler_dtype():
    sampler = tour.FrequencySampler(range(60))
    assert isinstance(sampler.sample(), int)


def test_facility_density_missing_activity():
    facility_df = pd.DataFrame({'id':[1,2,3,4], 'activity': ['home','work','home','delivery']})
    points = [Point((1,1)), Point((1,1)), Point((3,3)), Point((3,3))]
    facility_gdf = gp.GeoDataFrame(facility_df, geometry=points)

    zones_df = pd.DataFrame({'a':[1,2,3], 'b': [4,5,6]})
    polys = [
        Polygon(((0,0), (0,2), (2,2), (2,0))),
        Polygon(((2,2), (2,4), (4,4), (4,2))),
        Polygon(((4,4), (4,6), (6,6), (6,4)))
    ]
    zones_gdf = gp.GeoDataFrame(zones_df, geometry=polys)

    facility_zone = gp.sjoin(facility_gdf, zones_gdf, how='inner', op='intersects')

    o_density, d_density = tour.InputDemand().facility_density(facilities=facility_gdf,
                                                                      zones=zones_gdf,
                                                                      zone_id='a',
                                                                      o_activity='depot',
                                                                      d_activity='delivery')


    assert len(o_density) == 0
    assert len(d_density) > 0