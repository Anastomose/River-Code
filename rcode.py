"""Parse GPX files into memory and return json file for web display."""

import xml.etree.ElementTree as et
import json as js
import copy

PTDICT = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": []},
    "properties": {"name": None,
                   "category": None,
                   "description": None,
                   "marker-color": '#f7f7f7',
                   "marker-size": "small",
                   "marker-type": None,
                   "marker-symbol": str()
                   }
}

TGF = '{http://www.topografix.com/GPX/1/1}'  # prefix string for all nodes


def create_tree(fh):
    """Parse gpx file using ElementTree, returns xml obj."""
    with open(fh, 'rb') as fid:
        tree = et.parse(fid)
    return tree


def create_wpts(xmltree):
    """Create list of xmltree waypoint nodes from xmltree."""
    wpts = [n for n in xmltree.findall(TGF + 'wpt')]
    return wpts


def get_wpt_types(wpts):
    """Create list of waypoints from wpt list using .find('type')."""
    wpt_types = list()
    for wpts_i, wp in enumerate(wpts):
        try:
            wtype = wp.find(TGF + 'type')
            if wtype.text not in wpt_types:
                wpt_types.append(wtype.text)
        except AttributeError:
            print '{} has no type attribute'.format(wp.find(TGF + 'name').text)
            wpts.pop(wpts_i)
    return wpt_types


def create_feat(wpt, **kwargs):
    """Create geojson feature from xmlwaypoint.

    kwargs:
    markercolor: html marker color code
    """
    wd = copy.deepcopy(PTDICT)
    wd.get('geometry')['coordinates'] = [float(wpt.attrib.get('lon')),
                                         float(wpt.attrib.get('lat'))]

    xmltags = ['name', 'sym', 'type', 'desc']  # brittle here
    gjstags = ['name', 'marker-type', 'category', 'description']

    for xm, gj in zip(xmltags, gjstags):
        try:
            if wpt.find(TGF + xm).text != '\n':  # text tags only
                wd.get('properties')[gj] = wpt.find(TGF + xm).text

                if kwargs.get('markercolor'):
                    wd.get('properties')['marker-color'] = \
                        kwargs.get('markercolor')

                if kwargs.get('markersym'):
                    wd.get('properties')['marker-symbol'] = \
                        kwargs.get('markersym')
        except AttributeError:
            print 'Attribute error. {} does not have text.'.format(xm)

    return wd


def point_filter(wpt, **kwargs):
    """Filter fx checking xml point type matches."""
    try:
        if wpt.find(TGF + 'type').text != kwargs.get('pttype'):
            return False
        else:
            return True
    except AttributeError:
        return False


def create_geojson(feat_list, outfile='output1.json'):
    """Create geojson file."""
    gjs = {"type": "FeatureCollection", "features": feat_list}

    with open(outfile, 'wb') as fid:
        js.dump(gjs, fid)


if __name__ == '__main__':
    fids = ["dinosaur.gpx", "grandcanyon.gpx", "hellscanyon.gpx",
            "mainsalmon.gpx", "rogue.gpx", "selway.gpx", "tuolumne.gpx"]

    for fh in fids:
        features = list()
        # fh = r'selway.gpx'
        tree = create_tree(fh)  # parse xml tree
        wpts = create_wpts(tree)  # create waypoint list

        wpt_types = get_wpt_types(wpts)
        wpt_colors = ["#d53e4f", "#fc8d59", "#fee08b",
                      "#ffffbf", "#e6f598", "#99d594", "#3288bd"]
        wpt_dict = dict()

        for wt, cl in zip(wpt_types, wpt_colors[:len(wpt_types)]):
            print '{} will be color {}'.format(wt, cl)
            wpt_dict[wt] = [create_feat(wp, markercolor=cl)
                            for wp in wpts if point_filter(wp, pttype=wt)]

        for k in wpt_dict.keys():
            if k != 'Mileage':
                features += wpt_dict.get(k)

        create_geojson(features, fh.split('.')[0] + '.json')
