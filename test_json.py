import json

raw = """[ { "scene_number": 1, "script_segment": "Noor Women for Afghanistan is an organisation that supports the education of Afghan girls.", "visual_concept": "A collage of images showing a woman with a microphone speaking to a group of people in what appears to be a classroom setting. The images are arranged in a grid format, each depicting a different moment or angle of the same scene.", "suggested_clip": "Afghanistan_under_the_Taliban_｜DW_Documentary-(1080p25).mp4", "editing_tips": "Use a slow zoom effect to emphasize the speaker and the audience, cutting on action moments when the woman gestures or changes her expression." }, { "scene_number": 2, "script_segment": "In Dari, the national language of Afghanistan, Noor means light. Yet, a profound darkness has fallen over Afghanistan’s girls and women.", "visual_concept": "A collage of images showing a woman with a microphone speaking to a group of people in what appears to be a classroom setting. The images are arranged in a grid format, each depicting a different moment or angle of the same scene.", "suggested_clip": "Afghanistan_under_the_Taliban｜_DW_Documentary-(1080p25).mp4", "editing_tips": "Use a slow zoom effect to emphasize the speaker and the audience, cutting on action moments when the woman gestures or changes her expression." }, { "scene_number": 3, "script_segment": "FRANCE_24_report：The_Afghan_girls_defying_Taliban_bans_to_go_to_school•_FRANCE_24_English-(1080p25).mp4", "visual_concept": "A collage of images showing a woman with a microphone speaking to a group of people in what appears to be a classroom setting. The images are arranged in a grid format, each depicting a different moment or angle of the same scene.", "suggested_clip": "FRANCE_24_report：The_Afghan_girls_defying_Taliban_bans_to_go_to_school•FRANCE_24_English-(1080p25).mp4", "editing_tips": "Use a slow zoom effect to emphasize the speaker and the audience, cutting on action moments when the woman gestures or changes her expression." }, { "scene_number": 4, "script_segment": "The_Taliban’s_rules_for_women_in_Afghanistan｜Start_Here-(1080p25).mp4", "visual_concept": "A collage of images showing a woman with a microphone speaking to a group of people in what appears to be a classroom setting. The images are arranged in a grid format, each depicting a different moment or angle of the same scene.", "suggested_clip": "The_Taliban’s_rules_for_women_in_Afghanistan｜_Start_Here-(1080p25).mp4", "editing_tips": "Use a slow zoom effect to emphasize the speaker and the audience, cutting on action moments when the woman gestures or changes her expression." }, { "scene_number": 5, "script_segment": "Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", "visual_concept": "A collage of images showing a woman with a microphone speaking to a group of people in what appears to be a classroom setting. The images are arranged in a grid format, each depicting a different moment or angle of the same scene.", "suggested_clip": "Women’s rights being rolled back in Afghanistan - BBC News-(720p50).mp4", "editing_tips": "Use a slow zoom effect to emphasize the speaker and the audience, cutting on action moments when the woman gestures or changes her expression." }, { "scene_number": 6, "script_segment": "afghanistan_broll_compilation.mp4", "visual_concept": "A collage of images showing a woman with a microphone speaking to a group of people in what appears to be a classroom setting. The images are arranged in a grid format, each depicting a different moment or angle of the same scene.", "suggested_clip": "afghanistan_broll_compilation.mp4", "editing_tips": "Use a slow zoom effect to emphasize the speaker and the audience, cutting on action moments when the woman gestures or changes her expression." } ]"""

def _extract_json_array(text: str):
    start_idx = text.find('[')
    if start_idx == -1:
        return text
    
    count = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if not escape:
            if c == '"':
                in_string = not in_string
            elif not in_string:
                if c == '[':
                    count += 1
                elif c == ']':
                    count -= 1
                    if count == 0:
                        return text[start_idx:i+1]
        if c == '\\' and not escape:
            escape = True
        else:
            escape = False
    return text[start_idx:]

clean = _extract_json_array(raw)
try:
    data = json.loads(clean)
    print("Success")
except json.JSONDecodeError as e:
    print(f"Failed: {e}")
