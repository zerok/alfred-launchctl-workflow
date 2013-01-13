from xml.etree import ElementTree as ET
import subprocess
import collections


Service = collections.namedtuple('Service', 'pid status label')


def list_services(query=None):
    """
    This creates a list of all services that are currently available to the
    user.
    """
    result = ET.Element("items")
    matching_items = []
    for service in get_all_services():
        if not is_valid_service(service):
            continue
        if query:
            if query not in service.label.lower():
                continue
        matching_items.append(service)
        item = ET.SubElement(result, 'item')
        item.set('uid', service.label)
        title = ET.SubElement(item, 'title')
        title.text = u'{0} ({1})'.format(service.label, service.pid)
    if len(matching_items) == 1:
        return show_operations(matching_items[0])
    return ET.tostring(result)


def show_operations(service):
    """
    Returns an XML-string for Alfred containing all available operations for
    the provided service.
    """
    result = ET.Element('items')
    if service.pid != '-':
        stop_item = ET.SubElement(result, 'item')
        stop_item.set('uid', 'stop')
        stop_item.set('arg', 'stop {0}'.format(service.label))
        ET.SubElement(stop_item, 'title').text = 'Stop {0}'.format(service.label)
    else:
        start_item = ET.SubElement(result, 'item')
        start_item.set('uid', 'start')
        start_item.set('arg', 'start {0}'.format(service.label))
        ET.SubElement(start_item, 'title').text = 'Start {0}'.format(service.label)
    return ET.tostring(result)


def execute(query):
    """
    Executes the final command. The query itself has to consist of 2 parts:

    <start|stop> <appname>
    """
    query_parts = query.split(" ")
    cmd = query_parts[0]
    app = " ".join(query_parts[1:])
    if 0 == subprocess.check_call(['launchctl', cmd, app]):
        if cmd == 'stop':
            return "Stopped {0}".format(app)
        elif cmd == 'start':
            return "Started {0}".format(app)
        else:
            return "Success"
    else:
        return "Operation failed"


def get_all_services(raw_data=None):
    """
    Unfiltered generator for services provided by launchctl.
    """
    if raw_data is None:
        raw_data = subprocess.check_output('launchctl list', shell=True)
    for idx, line in enumerate(raw_data.split("\n")):
        if idx == 0:
            # The first line contains just header information
            continue
        line_parts = line.split("\t")
        if len(line_parts) != 3:
            continue
        yield Service(*line_parts)


def is_valid_service(service):
    return not service.label.startswith(('[', '0x', 'com.apple'))


def test_get_all_services():
    test_input = """PID	Status	Label
-	0	0x7fb99d019d00.mach_init.Inspector
126	-	0x7fb99d01db00.anonymous.launchd
14714	-	0x7fb99b41d340.anonymous.launchctl
-	0	com.apple.ZoomWindow
"""
    assert 4 == len(list(get_all_services(test_input)))


def test_is_valid_service():
    assert not is_valid_service(Service(None, None, '0xadsf'))
    assert not is_valid_service(Service(None, None, '[lala]asdf'))
    assert is_valid_service(Service(None, None, 'service'))
