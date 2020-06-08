""" Helper functions for manipulating geometric/geographical data """

import collections.abc
import functools

import numpy as np

from pyhelpers.ops import create_rotation_matrix


def wgs84_to_osgb36(longitude, latitude, **kwargs):
    """
    Convert latitude and longitude (WGS84) to British national grid (OSGB36).

    :param longitude: the longitude (abbr: long., λ, or lambda) of a point on Earth's surface
    :type longitude: float, int
    :param latitude: the latitude (abbr: lat., φ, or phi) of a point on Earth's surface
    :type latitude: float, int
    :return: geographic Cartesian coordinate (Easting, Northing) or (X, Y)
    :rtype: tuple [of length 2]

    Example::

        longitude, latitude = -0.12772404, 51.507407

        res = wgs84_to_osgb36(longitude, latitude)  # (530033.99829712, 180381.00751935126)
    """

    from pyproj import Transformer

    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth
    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum

    transformer = Transformer.from_crs(wgs84, osgb36)
    easting, northing = transformer.transform(latitude, longitude, **kwargs)

    return easting, northing


def osgb36_to_wgs84(easting, northing, **kwargs):
    """
    Convert British national grid (OSGB36) to latitude and longitude (WGS84).

    :param easting: Easting (X), eastward-measured distance (or the x-coordinate)
    :type easting: int, float
    :param northing: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northing: int, float
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple [of length 2]

    Example::

        easting, northing = 530034, 180381

        res = osgb36_to_wgs84(easting, northing)  # (-0.12772400574286874, 51.50740692743041)
    """

    from pyproj import Transformer

    osgb36 = 'EPSG:27700'  # UK Ordnance Survey, 1936 datum
    wgs84 = 'EPSG:4326'  # LonLat with WGS84 datum used by GPS units and Google Earth

    transformer = Transformer.from_crs(osgb36, wgs84)
    latitude, longitude = transformer.transform(easting, northing, **kwargs)

    return longitude, latitude


def wgs84_to_osgb36_calc(longitude, latitude):
    """
    Convert latitude and longitude (WGS84) to British National Grid (OSGB36) by calculation.

    This function is slightly modified from the original code available from
    [`WTOC-1 <http://blogs.casa.ucl.ac.uk/2014/12/26/>`_].

    :param longitude: the longitude (abbr: long., λ, or lambda) of a point on Earth's surface
    :type longitude: float, int
    :param latitude: the latitude (abbr: lat., φ, or phi) of a point on Earth's surface
    :type latitude: float, int
    :return: geographic Cartesian coordinate (Easting, Northing) or (X, Y)
    :rtype: tuple [of length 2]

    Example::

        longitude, latitude = -0.12772404, 51.507407

        res = wgs84_to_osgb36_calc(longitude, latitude)  # (530034.0010406997, 180381.0084845958)

        # cp. wgs84_to_osgb36(longitude, latitude)
    """

    # First convert to radians. These are on the wrong ellipsoid currently: GRS80. (Denoted by _1)
    lon_1, lat_1 = longitude * np.pi / 180, latitude * np.pi / 180

    # Want to convert to the Airy 1830 ellipsoid, which has the following:
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a_1, b_1 = 6378137.000, 6356752.3141
    e2_1 = 1 - (b_1 * b_1) / (a_1 * a_1)  # The eccentricity of the GRS80 ellipsoid
    nu_1 = a_1 / np.sqrt(1 - e2_1 * np.sin(lat_1) ** 2)

    # First convert to cartesian from spherical polar coordinates
    h = 0  # Third spherical coord.
    x_1 = (nu_1 + h) * np.cos(lat_1) * np.cos(lon_1)
    y_1 = (nu_1 + h) * np.cos(lat_1) * np.sin(lon_1)
    z_1 = ((1 - e2_1) * nu_1 + h) * np.sin(lat_1)

    # Perform Helmut transform (to go between GRS80 (_1) and Airy 1830 (_2))
    s = 20.4894 * 10 ** -6  # The scale factor -1
    # The translations along x,y,z axes respectively:
    tx, ty, tz = -446.448, 125.157, -542.060
    # The rotations along x,y,z respectively, in seconds:
    rxs, rys, rzs = -0.1502, -0.2470, -0.8421
    rx, ry, rz = rxs * np.pi / (180 * 3600.), rys * np.pi / (180 * 3600.), rzs * np.pi / (180 * 3600.)  # In radians
    x_2 = tx + (1 + s) * x_1 + (-rz) * y_1 + ry * z_1
    y_2 = ty + rz * x_1 + (1 + s) * y_1 + (-rx) * z_1
    z_2 = tz + (-ry) * x_1 + rx * y_1 + (1 + s) * z_1

    # Back to spherical polar coordinates from cartesian
    # Need some of the characteristics of the new ellipsoid
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a, b = 6377563.396, 6356256.909
    e2 = 1 - (b * b) / (a * a)  # The eccentricity of the Airy 1830 ellipsoid
    p = np.sqrt(x_2 ** 2 + y_2 ** 2)

    # Lat is obtained by an iterative procedure:
    latitude = np.arctan2(z_2, (p * (1 - e2)))  # Initial value
    lat_old = 2 * np.pi
    nu = 0
    while abs(latitude - lat_old) > 10 ** -16:
        latitude, lat_old = lat_old, latitude
        nu = a / np.sqrt(1 - e2 * np.sin(lat_old) ** 2)
        latitude = np.arctan2(z_2 + e2 * nu * np.sin(lat_old), p)

    # Lon and height are then pretty easy
    longitude = np.arctan2(y_2, x_2)
    # h = p / cos(lat) - nu

    # e, n are the British national grid coordinates - easting and northing
    # scale factor on the central meridian
    f0 = 0.9996012717
    # Latitude of true origin (radians)
    lat0 = 49 * np.pi / 180
    # Longitude of true origin and central meridian (radians)
    lon0 = -2 * np.pi / 180
    # Northing & easting of true origin (m)
    n0, e0 = -100000, 400000
    y = (a - b) / (a + b)

    # meridional radius of curvature
    rho = a * f0 * (1 - e2) * (1 - e2 * np.sin(latitude) ** 2) ** (-1.5)
    eta2 = nu * f0 / rho - 1

    m1 = (1 + y + (5 / 4) * y ** 2 + (5 / 4) * y ** 3) * (latitude - lat0)
    m2 = (3 * y + 3 * y ** 2 + (21 / 8) * y ** 3) * np.sin(latitude - lat0) * np.cos(latitude + lat0)
    m3 = ((15 / 8) * y ** 2 + (15 / 8) * y ** 3) * np.sin(2 * (latitude - lat0)) * np.cos(2 * (latitude + lat0))
    m4 = (35 / 24) * y ** 3 * np.sin(3 * (latitude - lat0)) * np.cos(3 * (latitude + lat0))

    # meridional arc
    m = b * f0 * (m1 - m2 + m3 - m4)

    i = m + n0
    ii = nu * f0 * np.sin(latitude) * np.cos(latitude) / 2
    iii = nu * f0 * np.sin(latitude) * np.cos(latitude) ** 3 * (5 - np.tan(latitude) ** 2 + 9 * eta2) / 24
    iii_a = nu * f0 * np.sin(latitude) * np.cos(latitude) ** 5 * (
            61 - 58 * np.tan(latitude) ** 2 + np.tan(latitude) ** 4) / 720
    iv = nu * f0 * np.cos(latitude)
    v = nu * f0 * np.cos(latitude) ** 3 * (nu / rho - np.tan(latitude) ** 2) / 6
    vi = nu * f0 * np.cos(latitude) ** 5 * (
            5 - 18 * np.tan(latitude) ** 2 + np.tan(latitude) ** 4 + 14 * eta2 -
            58 * eta2 * np.tan(latitude) ** 2) / 120

    y = i + ii * (longitude - lon0) ** 2 + iii * (longitude - lon0) ** 4 + iii_a * (longitude - lon0) ** 6
    x = e0 + iv * (longitude - lon0) + v * (longitude - lon0) ** 3 + vi * (longitude - lon0) ** 5

    return x, y


def osgb36_to_wgs84_calc(easting, northing):
    """
    Convert british national grid (OSGB36) to latitude and longitude (WGS84) by calculation.

    This function is slightly modified from the original code available from
    [`OTWC-1 <http://blogs.casa.ucl.ac.uk/2014/12/26/>`_].

    :param easting: Easting (X), eastward-measured distance (or the x-coordinate)
    :type easting: int, float
    :param northing: Northing (Y), northward-measured distance (or the y-coordinate)
    :type northing: int, float
    :return: geographic coordinate (Longitude, Latitude)
    :rtype: tuple [of length 2]

    Example::

        easting, northing = 530034, 180381

        res = osgb36_to_wgs84_calc(easting, northing)  # (-0.1277240422737611, 51.50740676560936)

        # cp. osgb36_to_wgs84(easting, northing)
    """

    # The Airy 180 semi-major and semi-minor axes used for OSGB36 (m)
    a, b = 6377563.396, 6356256.909
    # Scale factor on the central meridian
    f0 = 0.9996012717
    # Latitude of true origin (radians)
    lat0 = 49 * np.pi / 180
    # Longitude of true origin and central meridian (radians):
    lon0 = -2 * np.pi / 180
    # Northing and Easting of true origin (m):
    n0, e0 = -100000, 400000
    e2 = 1 - (b * b) / (a * a)  # eccentricity squared
    n = (a - b) / (a + b)

    # Initialise the iterative variables
    lat, m = lat0, 0

    while northing - n0 - m >= 0.00001:  # Accurate to 0.01mm
        lat += (northing - n0 - m) / (a * f0)
        m1 = (1 + n + (5. / 4) * n ** 2 + (5. / 4) * n ** 3) * (lat - lat0)
        m2 = (3 * n + 3 * n ** 2 + (21. / 8) * n ** 3) * np.sin(lat - lat0) * np.cos(lat + lat0)
        m3 = ((15. / 8) * n ** 2 + (15. / 8) * n ** 3) * np.sin(2 * (lat - lat0)) * np.cos(2 * (lat + lat0))
        m4 = (35. / 24) * n ** 3 * np.sin(3 * (lat - lat0)) * np.cos(3 * (lat + lat0))
        # meridional arc
        m = b * f0 * (m1 - m2 + m3 - m4)

    # transverse radius of curvature
    nu = a * f0 / np.sqrt(1 - e2 * np.sin(lat) ** 2)

    # meridional radius of curvature
    rho = a * f0 * (1 - e2) * (1 - e2 * np.sin(lat) ** 2) ** (-1.5)
    eta2 = nu / rho - 1

    sec_lat = 1. / np.cos(lat)
    vii = np.tan(lat) / (2 * rho * nu)
    viii = np.tan(lat) / (24 * rho * nu ** 3) * (5 + 3 * np.tan(lat) ** 2 + eta2 - 9 * np.tan(lat) ** 2 * eta2)
    ix = np.tan(lat) / (720 * rho * nu ** 5) * (61 + 90 * np.tan(lat) ** 2 + 45 * np.tan(lat) ** 4)
    x = sec_lat / nu
    xi = sec_lat / (6 * nu ** 3) * (nu / rho + 2 * np.tan(lat) ** 2)
    xii = sec_lat / (120 * nu ** 5) * (5 + 28 * np.tan(lat) ** 2 + 24 * np.tan(lat) ** 4)
    xiia = sec_lat / (5040 * nu ** 7) * (61 + 662 * np.tan(lat) ** 2 + 1320 * np.tan(lat) ** 4 + 720 * np.tan(lat) ** 6)
    de = easting - e0

    # These are on the wrong ellipsoid currently: Airy1830. (Denoted by _1)
    lat_1 = lat - vii * de ** 2 + viii * de ** 4 - ix * de ** 6
    lon_1 = lon0 + x * de - xi * de ** 3 + xii * de ** 5 - xiia * de ** 7

    """ Want to convert to the GRS80 ellipsoid. """
    # First convert to cartesian from spherical polar coordinates
    h = 0  # Third spherical coord.
    x_1 = (nu / f0 + h) * np.cos(lat_1) * np.cos(lon_1)
    y_1 = (nu / f0 + h) * np.cos(lat_1) * np.sin(lon_1)
    z_1 = ((1 - e2) * nu / f0 + h) * np.sin(lat_1)

    # Perform Helmut transform (to go between Airy 1830 (_1) and GRS80 (_2))
    s = -20.4894 * 10 ** -6  # The scale factor -1
    # The translations along x,y,z axes respectively
    tx, ty, tz = 446.448, -125.157, + 542.060
    # The rotations along x,y,z respectively, in seconds
    rxs, rys, rzs = 0.1502, 0.2470, 0.8421
    rx, ry, rz = rxs * np.pi / (180 * 3600.), rys * np.pi / (180 * 3600.), rzs * np.pi / (180 * 3600.)  # In radians
    x_2 = tx + (1 + s) * x_1 + (-rz) * y_1 + ry * z_1
    y_2 = ty + rz * x_1 + (1 + s) * y_1 + (-rx) * z_1
    z_2 = tz + (-ry) * x_1 + rx * y_1 + (1 + s) * z_1

    # Back to spherical polar coordinates from cartesian
    # Need some of the characteristics of the new ellipsoid
    # The GSR80 semi-major and semi-minor axes used for WGS84(m)
    a_2, b_2 = 6378137.000, 6356752.3141
    e2_2 = 1 - (b_2 * b_2) / (a_2 * a_2)  # The eccentricity of the GRS80 ellipsoid
    p = np.sqrt(x_2 ** 2 + y_2 ** 2)

    # Lat is obtained by an iterative procedure:
    lat = np.arctan2(z_2, (p * (1 - e2_2)))  # Initial value
    lat_old = 2 * np.pi
    while abs(lat - lat_old) > 10 ** -16:
        lat, lat_old = lat_old, lat
        nu_2 = a_2 / np.sqrt(1 - e2_2 * np.sin(lat_old) ** 2)
        lat = np.arctan2(z_2 + e2_2 * nu_2 * np.sin(lat_old), p)

    # Lon and height are then pretty easy
    long = np.arctan2(y_2, x_2)
    # h = p / cos(lat) - nu_2

    # Print the results
    # print([(lat - lat_1) * 180 / pi, (lon - lon_1) * 180 / pi])

    # Convert to degrees
    long = long * 180 / np.pi
    lat = lat * 180 / np.pi

    return long, lat


def get_midpoint(x1, y1, x2, y2, as_geom=False):
    """
    Get the midpoint between two points (applicable for vectorized computation).

    :param x1: longitude(s) or easting(s) of a point (an array of points)
    :type x1: float, int, numpy.ndarray
    :param y1: latitude(s) or northing(s) of a point (an array of points)
    :type y1: float, int, numpy.ndarray
    :param x2: longitude(s) or easting(s) of another point (another array of points)
    :type x2: float, int, numpy.ndarray
    :param y2: latitude(s) or northing(s) of another point (another array of points)
    :type y2: float, int, numpy.ndarray
    :param as_geom: whether to return
        `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_, defaults to ``False``
    :type as_geom: bool
    :return: the midpoint between ``(x1, y1)`` and ``(x2, y2)`` (or midpoints between two sequences of points)
    :rtype: numpy.ndarray, shapely.geometry.Point, list [of shapely.geometry.Point]

    Examples::

        from shapely.geometry import Point

        x1, y1 = 1.5429, 52.6347
        x2, y2 = 1.4909, 52.6271
        midpoint = np.array([1.5169, 52.6309])

        as_geom = False
        res_0 = get_midpoint(x1, y1, x2, y2, as_geom)
        (res_0 == midpoint).all()  # True

        as_geom = True
        res_1 = get_midpoint(x1, y1, x2, y2, as_geom=True)
        res_1 == Point(midpoint)  # True

        x1, y1 = np.array([1.5429, 1.4909]), np.array([52.6347, 52.6271])
        x2, y2 = np.array([2.5429, 2.4909]), np.array([53.6347, 53.6271])
        midpoint = np.array([[2.0429, 53.1347], [1.9909, 53.1271]])

        as_geom = False
        res_0 = get_midpoint(x1, y1, x2, y2, as_geom)
        (res_0 == midpoint).all()  # True

        as_geom = True
        res_1 = get_midpoint(x1, y1, x2, y2, as_geom=True)
        res_1 == [Point(x) for x in midpoint]  # True
    """

    mid_pts = (x1 + x2) / 2, (y1 + y2) / 2

    if as_geom:

        from shapely.geometry import Point

        if all(isinstance(x, np.ndarray) for x in mid_pts):
            midpoint = [Point(x_, y_) for x_, y_ in zip(list(mid_pts[0]), list(mid_pts[1]))]
        else:
            midpoint = Point(mid_pts)

    else:
        midpoint = np.array(mid_pts).T

    return midpoint


def transform_geom_point_type(*pts, as_geom=True):
    """
    Transform iterable to `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_ type,
    or the other way round.

    :param pts: points
    :type pts: iterable [e.g. list of lists/tuples or shapely.geometry.Points]
    :param as_geom: whether to return point(s) as
        `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_, defaults to ``True``
    :type as_geom: bool
    :return: a sequence of points (incl. None, if errors occur)
    :rtype: types.GeneratorType

    Examples::

        from shapely.geometry import Point

        pt_x = 1.5429, 52.6347
        pt_y = 1.4909, 52.6271

        as_geom = True
        geom_points_0 = transform_geom_point_type(pt_x, pt_y, as_geom=as_geom)
        [(x.x, x.y) for x in geom_points_0] == [pt_x, pt_y]  # True

        as_geom = False
        geom_points_1 = transform_geom_point_type(pt_x, pt_y, as_geom=as_geom)
        [(x, y) for x, y in geom_points_1] == [pt_x, pt_y]  # True

        pt_x = Point(1.5429, 52.6347)
        pt_y = Point(1.4909, 52.6271)

        as_geom = True
        geom_points_2 = transform_geom_point_type(pt_x, pt_y, as_geom=as_geom)
        [x for x in geom_points_2] == [pt_x, pt_y]  # True

        as_geom = False
        geom_points_3 = transform_geom_point_type(pt_x, pt_y, as_geom=as_geom)
        [Point(x) for x in geom_points_3] == [pt_x, pt_y]  # True
    """

    from shapely.geometry import Point

    if as_geom:
        for pt in pts:
            if isinstance(pt, Point):
                pt_ = pt
            elif isinstance(pt, collections.abc.Iterable):
                assert len(list(pt)) == 2
                pt_ = Point(pt)
            else:
                pt_ = None
            yield pt_
    else:
        for pt in pts:
            if isinstance(pt, Point):
                pt_ = pt.x, pt.y
            elif isinstance(pt, collections.abc.Iterable):
                assert len(list(pt)) == 2
                pt_ = pt
            else:
                pt_ = None
            yield pt_


def get_geometric_midpoint(pt_x, pt_y, as_geom=True):
    """
    Get the midpoint between two points.

    :param pt_x: a point
    :type pt_x: shapely.geometry.Point, array-like [of length 2]
    :param pt_y: a point
    :type pt_y: shapely.geometry.Point, array-like [of length 2]
    :param as_geom: whether to return
        `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_, defaults to ``True``
    :type as_geom: bool
    :return: the midpoint between ``pt_x`` and ``pt_y``
    :rtype: array-like, shapely.geometry.Point, None

    Examples::

        pt_x = 1.5429, 52.6347
        pt_y = 1.4909, 52.6271
        midpoint = 1.5169, 52.6309

        as_geom = False
        res_0 = get_geometric_midpoint(pt_x, pt_y, as_geom)
        res_0 == midpoint  # True

        as_geom = True
        res_1 = get_geometric_midpoint(pt_x, pt_y, as_geom)
        res_1 == Point(midpoint)  # True
    """

    pt_x_, pt_y_ = transform_geom_point_type(pt_x, pt_y, as_geom=True)

    midpoint = (pt_x_.x + pt_y_.x) / 2, (pt_x_.y + pt_y_.y) / 2

    if as_geom:
        from shapely.geometry import Point
        midpoint = Point(midpoint)

    return midpoint


def get_geometric_midpoint_calc(pt_x, pt_y, as_geom=False):
    """
    Get the midpoint between two points by pure calculation.
    See also these references: [`GGMC-1 <http://code.activestate.com/recipes/577713-midpoint-of-two-gps-points/>`_] and
    [`GGMC-2 <http://www.movable-type.co.uk/scripts/latlong.html>`_].

    :param pt_x: a point
    :type pt_x: shapely.geometry.Point, array-like [of length 2]
    :param pt_y: a point
    :type pt_y: shapely.geometry.Point, array-like [of length 2]
    :param as_geom: whether to return
        `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_. defaults to ``False``
    :type as_geom: bool
    :return: the midpoint between ``pt_x`` and ``pt_y``
    :rtype: tuple, shapely.geometry.Point, None

    Examples::

        from shapely.geometry import Point

        pt_x = 1.5429, 52.6347
        pt_y = 1.4909, 52.6271
        midpoint = (1.5168977420748175, 52.630902845583094)

        res_0 = get_geometric_midpoint_calc(pt_x, pt_y)
        res_0 == midpoint  # True

        as_geom = True
        res_1 = get_geometric_midpoint_calc(pt_x, pt_y, as_geom)
        res_1 == Point(midpoint)  # True
    """

    pt_x_, pt_y_ = transform_geom_point_type(pt_x, pt_y, as_geom=True)

    # Input values as degrees, convert them to radians
    lon_1, lat_1 = np.radians(pt_x_.x), np.radians(pt_x_.y)
    lon_2, lat_2 = np.radians(pt_y_.x), np.radians(pt_y_.y)

    b_x, b_y = np.cos(lat_2) * np.cos(lon_2 - lon_1), np.cos(lat_2) * np.sin(lon_2 - lon_1)
    lat_3 = np.arctan2(np.sin(lat_1) + np.sin(lat_2), np.sqrt((np.cos(lat_1) + b_x) * (np.cos(lat_1) + b_x) + b_y ** 2))
    long_3 = lon_1 + np.arctan2(b_y, np.cos(lat_1) + b_x)

    midpoint = np.degrees(long_3), np.degrees(lat_3)

    if as_geom:
        from shapely.geometry import Point
        midpoint = Point(midpoint)

    return midpoint


def calc_distance_on_unit_sphere(pt_x, pt_y):
    """
    Calculate distance between two points.

    This function is modified from the original code available from
    [`CDOUS-1 <http://www.johndcook.com/blog/python_longitude_latitude/>`_].
    It assumes the earth is perfectly spherical and returns the distance based on each point's longitude and latitude.

    :param pt_x: a point
    :type pt_x: shapely.geometry.Point, array-like [of length 2]
    :param pt_y: a point
    :type pt_y: shapely.geometry.Point, array-like [of length 2]
    :return: distance (in miles) between ``pt_x`` and ``pt_y`` (relative to the earth's radius)
    :rtype: float

    Examples::

        pt_x = 1.5429, 52.6347
        pt_y = 1.4909, 52.6271

        arc_length = calc_distance_on_unit_sphere(pt_x, pt_y)  # 2.243709962588554
    """

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = np.pi / 180.0

    from shapely.geometry import Point

    if not all(isinstance(x, Point) for x in (pt_x, pt_y)):
        try:
            pt_x = Point(pt_x)
            pt_y = Point(pt_y)
        except Exception as e:
            print(e)
            return None

    # phi = 90 - latitude
    phi1 = (90.0 - pt_x.y) * degrees_to_radians
    phi2 = (90.0 - pt_y.y) * degrees_to_radians

    # theta = longitude
    theta1 = pt_x.x * degrees_to_radians
    theta2 = pt_y.x * degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) = sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cosine = (np.sin(phi1) * np.sin(phi2) * np.cos(theta1 - theta2) + np.cos(phi1) * np.cos(phi2))
    arc_length = np.arccos(cosine) * 3960  # in miles

    # Remember to multiply arc by the radius of the earth in your set of units to get length.
    return arc_length


def calc_hypotenuse_distance(pt_x, pt_y):
    """
    Calculate hypotenuse given two points (the right angled triangle, given its side and perpendicular).
    This is the length of the vector from the ``orig_pt`` to ``dest_pt``.

    ``numpy.hypot(x, y)`` return the Euclidean norm, ``sqrt(x*x + y*y)``.
    See also [`CHD-1 <https://numpy.org/doc/stable/reference/generated/numpy.hypot.html>`_]

    :param pt_x: a point
    :type pt_x: shapely.geometry.Point, array-like [of length 2]
    :param pt_y: a point
    :type pt_y: shapely.geometry.Point, array-like [of length 2]
    :return: hypotenuse
    :rtype: float

    Examples::

        pt_x = 1.5429, 52.6347
        pt_y = 1.4909, 52.6271

        hypot_dist = calc_hypotenuse_distance(pt_x, pt_y)  # 0.05255244999046248
    """

    pt_x_, pt_y_ = transform_geom_point_type(pt_x, pt_y, as_geom=False)
    x_diff, y_diff = pt_x_[0] - pt_y_[0], pt_x_[1] - pt_y_[1]
    hypot_dist = np.hypot(x_diff, y_diff)
    return hypot_dist


def find_closest_point_from(pt, ref_pts, as_geom=False):
    """
    Find the closest point of the given point to a list of points.

    :param pt: (longitude, latitude)
    :type pt: tuple, list
    :param ref_pts: a sequence of reference (tuple/list of length 2) points
    :type ref_pts: tuple, list, iterable
    :param as_geom: whether to return
        `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_, defaults to ``False``
    :type as_geom: bool
    :return: the point closest to ``pt``
    :rtype: tuple, list, shapely.geometry.Point

    Examples::

        from shapely.geometry import Point

        pt = (2.5429, 53.6347)
        ref_pts = ((1.5429, 52.6347),
                   (1.4909, 52.6271),
                   (1.4248, 52.63075))

        closest_point = find_closest_point_from(pt, ref_pts)  # (1.5429, 52.6347)

        pt = Point((2.5429, 53.6347))
        ref_pts = (Point((1.5429, 52.6347)), Point((1.4909, 52.6271)), Point((1.4248, 52.63075)))

        closest_point = find_closest_point_from(pt, ref_pts)  # (1.5429, 52.6347)

        res = find_closest_point_from(pt, ref_pts, as_geom=True)
        (res.x, res.y) == closest_point  # True
    """

    from shapely.geometry import Point

    pt_ = (pt.x, pt.y) if isinstance(pt, Point) else pt
    ref_pts_ = ((pt.x, pt.y) for pt in ref_pts) if any(isinstance(x, Point) for x in ref_pts) else ref_pts

    # Find the min value using the distance function with coord parameter
    closest_point = min(ref_pts_, key=functools.partial(calc_hypotenuse_distance, pt_))

    if as_geom:
        closest_point = Point(closest_point)

    return closest_point


def find_closest_points_between(pts, ref_pts, k=1, as_geom=False, **kwargs):
    """
    Find the closest points from a given list of reference points (applicable for vectorized computation).
    See also [`FCPB-1 <https://gis.stackexchange.com/questions/222315>`_].

    :param pts: an array of points
    :type pts: numpy.ndarray [of size (n, 2)]
    :param ref_pts: an array of reference points
    :type ref_pts: numpy.ndarray [of size (n, 2)]
    :param k: (up to) the ``k``-th nearest neighbour(s), defaults to ``1``
    :type k: integer, list of integer
    :param as_geom: whether to return
        `shapely.geometry.Point <https://shapely.readthedocs.io/en/latest/manual.html#points>`_, defaults to ``False``
    :type as_geom: bool
    :param kwargs: optional arguments of
        `scipy.spatial.cKDTree <https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html>`_
    :return: the closest point(s)
    :rtype: numpy.ndarray, list

    Examples::

        import numpy as np

        pts = np.array([[1.5429, 52.6347],
                        [1.4909, 52.6271],
                        [1.4248, 52.63075]])

        ref_pts = np.array([[2.5429, 53.6347],
                            [2.4909, 53.6271],
                            [2.4248, 53.63075]])
        k = 1
        closest_points = np.array([[2.4248, 53.63075],
                                   [2.4248, 53.63075],
                                   [2.4248, 53.63075]])

        as_geom = False
        res = find_closest_points_between(pts, ref_pts, k, as_geom)
        (res == closest_points).all()  # True

        as_geom = True
        res = find_closest_points_between(pts, ref_pts, k, as_geom)
        [np.array(x) for x in res_1] == closest_points  # True
    """

    if isinstance(ref_pts, np.ndarray):
        ref_pts_ = ref_pts
    else:
        ref_pts_ = np.concatenate([np.array(geom.coords) for geom in ref_pts])

    from scipy.spatial.ckdtree import cKDTree

    ref_ckd_tree = cKDTree(ref_pts_, **kwargs)
    distances, indices = ref_ckd_tree.query(pts, k=k)  # returns (distance, index)

    if as_geom:
        from shapely.geometry import Point
        closest_points = [Point(ref_pts_[i]) for i in indices]
    else:
        closest_points = np.array([ref_pts_[i] for i in indices])

    return closest_points


def get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Get the four vertices of a square given its centre and side length.
    See also [`GSV-1 <https://stackoverflow.com/questions/22361324/>`_].

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int, float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int, float
    :param side_length: side length of a square
    :type side_length: int, float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree), defaults to ``0``
    :type rotation_theta: int, float
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    Examples::

        ctr_x, ctr_y = -5.9375, 56.8125
        side_length = 0.125
        rotation_theta = 0

        vertices_ = np.array([[-6.   , 56.75 ],
                              [-6.   , 56.875],
                              [-5.875, 56.875],
                              [-5.875, 56.75 ]])

        res = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta=0)
        # (res == vertices_).all()

        vertices_ = np.array([[-5.96037659, 56.72712341],
                              [-6.02287659, 56.83537659],
                              [-5.91462341, 56.89787659],
                              [-5.85212341, 56.78962341]])

        rotation_theta = 30  # rotate the square by 30° (anticlockwise)
        res = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta)
        # (np.round(res, 8) == vertices_).all()
    """

    sides = np.ones(2) * side_length

    rotation_matrix = create_rotation_matrix(np.deg2rad(rotation_theta))

    vertices = [np.array([ctr_x, ctr_y]) +
                functools.reduce(np.dot, [rotation_matrix, create_rotation_matrix(-0.5 * np.pi * x), sides / 2])
                for x in range(4)]
    vertices_ = np.array(vertices, dtype=np.float64)

    return vertices_


def get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta=0):
    """
    Get the four vertices of a square given its centre and side length (by elementary calculation).
    See also [`GSVC-1 <https://math.stackexchange.com/questions/1490115>`_].

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int, float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int, float
    :param side_length: side length of a square
    :type side_length: int, float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree), defaults to ``0``
    :type rotation_theta: int, float
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    Examples::

        import numpy as np

        ctr_x, ctr_y = -5.9375, 56.8125
        side_length = 0.125

        rotation_theta = 0
        vertices = np.array([[-6., 56.75], [-6., 56.875], [-5.875, 56.875], [-5.875, 56.75]])

        res = get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta)
        # (res == vertices).all()

        rotation_theta = 30  # rotate the square by 30° (anticlockwise)
        vertices = np.array([[-5.96037659, 56.72712341],
                             [-6.02287659, 56.83537659],
                             [-5.91462341, 56.89787659],
                             [-5.85212341, 56.78962341]])

        res = get_square_vertices_calc(ctr_x, ctr_y, side_length, rotation_theta)
        # (np.round(res, 8) == vertices).all()
    """

    theta_rad = np.deg2rad(rotation_theta)

    ll = (ctr_x + 1 / 2 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)),
          ctr_y - 1 / 2 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)))
    ul = (ctr_x - 1 / 2 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)),
          ctr_y - 1 / 2 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)))
    ur = (ctr_x - 0.5 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)),
          ctr_y + 0.5 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)))
    lr = (ctr_x + 0.5 * side_length * (np.sin(theta_rad) + np.cos(theta_rad)),
          ctr_y + 0.5 * side_length * (np.sin(theta_rad) - np.cos(theta_rad)))

    vertices = np.array([ll, ul, ur, lr])

    return vertices


def sketch_square(ctr_x, ctr_y, side_length=None, rotation_theta=0, fig_size=(6.4, 4.8), annotation=True,
                  ret_vertices=False, **kwargs):
    """
    Visualise the square given its centre point, four vertices and rotation angle (in degree).

    :param ctr_x: x coordinate of a square centre
    :type ctr_x: int, float
    :param ctr_y: y coordinate of a square centre
    :type ctr_y: int, float
    :param side_length: side length of a square
    :type side_length: int, float
    :param rotation_theta: rotate (anticlockwise) the square by ``rotation_theta`` (in degree), defaults to ``0``
    :type rotation_theta: int, float
    :param fig_size: figure size, defaults to ``(6.4, 4.8)``
    :type fig_size: tuple, list
    :param annotation: whether to annotate vertices of the square, defaults to ``True``
    :type annotation: bool
    :param ret_vertices: whether to return the vertices of the square, defaults to ``False``
    :type ret_vertices: bool
    :param kwargs: optional arguments of
        `matplotlib.pyplot.subplots <https://matplotlib.org/3.2.1/api/_as_gen/matplotlib.pyplot.subplots.html>`_
    :return: vertices of the square as an array([ll, ul, ur, lr])
    :rtype: numpy.ndarray

    Examples::

        ctr_x, ctr_y = 1, 1
        side_length = 2
        rotation_theta = 0

        sketch_square(ctr_x, ctr_y, side_length, rotation_theta, fig_size=(6.4, 4.8))

        sketch_square(ctr_x, ctr_y, side_length, rotation_theta, fig_size=(8, 8))

        rotation_theta = 15
        sketch_square(ctr_x, ctr_y, side_length, rotation_theta, fig_size=(8, 8), annotation=False)
    """

    import matplotlib.pyplot as plt
    import matplotlib.ticker

    vertices = get_square_vertices(ctr_x, ctr_y, side_length, rotation_theta)
    vertices_ = np.append(vertices, [tuple(vertices[0])], axis=0)

    _, ax = plt.subplots(1, 1, figsize=fig_size, **kwargs)
    ax.plot(ctr_x, ctr_y, 'o', markersize=10)
    ax.annotate("({0:.2f}, {0:.2f})".format(ctr_x, ctr_y), xy=(ctr_x, ctr_y))

    if rotation_theta == 0:
        ax.plot(vertices_[:, 0], vertices_[:, 1], 'o-')
    else:
        ax.plot(vertices_[:, 0], vertices_[:, 1], 'o-', label="$\\theta$ = {}°".format(rotation_theta))
        ax.legend(loc="best")

    if annotation:
        for x, y in zip(vertices[:, 0], vertices[:, 1]):
            ax.annotate("({0:.2f}, {0:.2f})".format(x, y), xy=(x, y))

    ax.axis("equal")

    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

    plt.tight_layout()

    if ret_vertices:
        return vertices
