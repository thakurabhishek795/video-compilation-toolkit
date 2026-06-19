import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

def generate_fcpxml(media_dir, clips):
    def sec_to_fcpxml_time(time_str):
        if not time_str or time_str == "Unknown":
            return "0s"
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            total_sec = h * 3600 + m * 60 + s
            if total_sec == int(total_sec):
                return f"{int(total_sec)}s"
            return f"{int(total_sec * 1000)}/1000s"
        return "0s"

    fcpxml = ET.Element("fcpxml", version="1.9")
    resources = ET.SubElement(fcpxml, "resources")
    ET.SubElement(resources, "format", id="r1", name="FFVideoFormat1080p25", frameDuration="1/25s", width="1920", height="1080")

    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name="B-Roll Compilation")
    project = ET.SubElement(event, "project", name="Unified Storyboard")
    sequence = ET.SubElement(project, "sequence", format="r1", tcStart="0s", tcFormat="NDF")
    spine = ET.SubElement(sequence, "spine")

    assets = {}
    asset_idx = 2
    current_offset_sec = 0.0

    for clip in clips:
        filename = clip['File Name']
        if filename not in assets:
            abs_path = os.path.abspath(os.path.join(media_dir, filename))
            asset_id = f"r{asset_idx}"
            assets[filename] = asset_id
            asset_idx += 1
            ET.SubElement(resources, "asset", id=asset_id, name=filename, src=f"file://{abs_path}", hasVideo="1", hasAudio="1")
        else:
            asset_id = assets[filename]

        start_sec_str = sec_to_fcpxml_time(clip['Start Time'])
        duration_sec_str = sec_to_fcpxml_time(clip['Duration'])
        
        dur_parts = clip['Duration'].split(":")
        dur_val = int(dur_parts[0])*3600 + int(dur_parts[1])*60 + float(dur_parts[2]) if len(dur_parts) == 3 else 0.0
        
        offset_sec_str = f"{int(current_offset_sec * 1000)}/1000s" if current_offset_sec != int(current_offset_sec) else f"{int(current_offset_sec)}s"
        
        ET.SubElement(spine, "asset-clip", ref=asset_id, offset=offset_sec_str, name=filename, start=start_sec_str, duration=duration_sec_str, format="r1")
        
        current_offset_sec += dur_val

    xml_str = ET.tostring(fcpxml, 'utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="    ")
    
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n' + '\n'.join(pretty_xml.split('\n')[1:])

clips = [
    {"File Name": "12647598_1920_1080_50fps.mp4", "Start Time": "00:00:00", "Duration": "00:00:10"},
    {"File Name": "Afghanistan under the Taliban | DW Documentary-(1080p25).mp4", "Start Time": "00:01:30", "Duration": "00:00:20"},
]
print(generate_fcpxml("/Users/athakur/Downloads/taliban", clips))
