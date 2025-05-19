from datetime import datetime, timedelta

def convert_to_gmt(input_time):
    """
    Convert time from a specified timezone to GMT+2.
    
    Args:
        input_time (str): Input time in format 'TIMEZONE HH:MM'
        
    Returns:
        str: Converted time or error message
    """
    timezone_offsets = {
        'GMT': 0,
        'UTC': 0,
        'ECT': 1,
        'EET': 2,
        'ART': 2,
        'EAT': 3,
        'MET': 3.5,
        'NET': 4,
        'PLT': 5,
        'IST': 5.5,
        'BST': 6,
        'VST': 7,
        'CTT': 8,
        'JST': 9,
        'ACT': 9.5,
        'AET': 10,
        'SST': 11,
        'NST': 12,
        'MIT': -11,
        'HST': -10,
        'AST': -9,
        'PST': -8,
        'PNT': -7,
        'MST': -7,
        'CST': -6,
        'EST': -5,
        'IET': -5,
        'PRT': -4,
        'CNT': -3.5,
        'AGT': -3,
        'BET': -3,
        'CAT': -1,
    }

    try:
        # Split and format input, convert to datetime
        timezone, time_str = input_time.split()
        timezone = timezone.upper()
        time = datetime.strptime(time_str, '%H:%M')

        if timezone not in timezone_offsets:
            raise ValueError(f"{timezone} is not a valid timezone")

        # Calculate offset difference
        offset_diff = timezone_offsets[timezone] - 2
        converted_time = time + timedelta(hours=offset_diff)

        # Format return string
        converted_time_str = converted_time.strftime('%H:%M')
        offset_sign = '+' if offset_diff >= 0 else '-'
        offset_str = f"{offset_sign}{abs(offset_diff)}"

        return f"{converted_time_str} ({offset_str} hours from {time_str})"
    except ValueError as e:
        return str(e)