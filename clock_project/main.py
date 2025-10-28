from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import pytz
import math

app = Flask(__name__)

# ============================================
# DOUBLY CIRCULAR LINKED LIST IMPLEMENTATION
# ============================================

class ClockNode:
    
    def __init__(self, city_name, timezone_str, image_filename):
        self.city_name = city_name
        self.timezone_str = timezone_str
        self.timezone = pytz.timezone(timezone_str)
        self.image_filename = image_filename
        self.next_clock = None
        self.previous_clock = None
        self.time_offset = timedelta(0)  # Offset for manual time adjustment
        self.is_modified = False  # Track if time has been manually modified
    
    def get_current_time(self):
        """Get current time in this timezone with manual offset applied"""
        base_time = datetime.now(self.timezone)
        return base_time + self.time_offset
    
    def set_time_offset(self, hours=0, minutes=0):
        """Set manual time offset for this clock"""
        self.time_offset = timedelta(hours=hours, minutes=minutes)
        self.is_modified = hours != 0 or minutes != 0
    
    def reset_time_offset(self):
        """Reset time to actual timezone time"""
        self.time_offset = timedelta(0)
        self.is_modified = False
    
    def is_daytime(self):
        """Check if it's daytime (6 AM to 6 PM)"""
        current_hour = self.get_current_time().hour
        return 6 <= current_hour < 18
    
    def get_clock_data(self):
        """Get all clock information as dictionary"""
        current_time = self.get_current_time()
        return {
            'city': self.city_name,
            'timezone': self.timezone_str,
            'hour': current_time.hour,
            'minute': current_time.minute,
            'second': current_time.second,
            'is_day': self.is_daytime(),
            'image': self.image_filename,
            'hour_angle': self.calculate_hour_angle(current_time),
            'minute_angle': self.calculate_minute_angle(current_time),
            'second_angle': self.calculate_second_angle(current_time),
            'formatted_time': current_time.strftime('%I:%M %p'),
            'date': current_time.strftime('%B %d, %Y'),
            'day_of_week': current_time.strftime('%A'),
            'is_modified': self.is_modified,
            'offset_hours': int(self.time_offset.total_seconds() // 3600),
            'offset_minutes': int((self.time_offset.total_seconds() % 3600) // 60)
        }
    
    @staticmethod
    def calculate_hour_angle(time):
        """Calculate hour hand angle (0-360 degrees)"""
        hour = time.hour % 12
        minute = time.minute
        return (hour * 30) + (minute * 0.5)
    
    @staticmethod
    def calculate_minute_angle(time):
        """Calculate minute hand angle (0-360 degrees)"""
        return time.minute * 6
    
    @staticmethod
    def calculate_second_angle(time):
        
        return time.second * 6


class CircularClockList:
    
    def __init__(self):
        self.head_clock = None
        self.clock_count = 0
    
    def add_clock(self, city_name, timezone_str, image_filename):
        new_clock = ClockNode(city_name, timezone_str, image_filename)
        
        if self.head_clock is None:
            new_clock.next_clock = new_clock
            new_clock.previous_clock = new_clock
            self.head_clock = new_clock
        else:
            tail_clock = self.head_clock.previous_clock
            
            tail_clock.next_clock = new_clock
            new_clock.previous_clock = tail_clock
            new_clock.next_clock = self.head_clock
            self.head_clock.previous_clock = new_clock
        
        self.clock_count += 1
    
    def get_all_clocks_data(self):
        if self.head_clock is None:
            return []
        
        clocks_data = []
        current_clock = self.head_clock
        
        for _ in range(self.clock_count):
            clocks_data.append(current_clock.get_clock_data())
            current_clock = current_clock.next_clock
        
        return clocks_data
    
    def get_dominant_theme(self):
        if self.head_clock is None:
            return 'day'
        
        day_count = 0
        current_clock = self.head_clock
        
        for _ in range(self.clock_count):
            if current_clock.is_daytime():
                day_count += 1
            current_clock = current_clock.next_clock
        
        return 'day' if day_count >= (self.clock_count / 2) else 'night'
    
    def get_clock_at_index(self, index):
        
        if self.head_clock is None or index < 0 or index >= self.clock_count:
            return None
        
        current_clock = self.head_clock
        for _ in range(index):
            current_clock = current_clock.next_clock
        
        return current_clock
    
    def calculate_time_difference(self, index1, index2):
        
        clock1 = self.get_clock_at_index(index1)
        clock2 = self.get_clock_at_index(index2)
        
        if not clock1 or not clock2:
            return None
        
        time1 = clock1.get_current_time()
        time2 = clock2.get_current_time()
        
        # Calculate difference in hours
        diff = (time2.hour - time1.hour) + (time2.minute - time1.minute) / 60
        
        return {
            'clock1': clock1.city_name,
            'clock2': clock2.city_name,
            'difference_hours': round(diff, 2),
            'difference_text': self._format_time_difference(diff)
        }
    
    @staticmethod
    def _format_time_difference(hours):
        abs_hours = abs(hours)
        whole_hours = int(abs_hours)
        minutes = int((abs_hours - whole_hours) * 60)
        
        direction = "ahead" if hours > 0 else "behind"
        
        if minutes == 0:
            return f"{whole_hours} hours {direction}"
        else:
            return f"{whole_hours}h {minutes}m {direction}"
    
    def find_optimal_meeting_time(self, start_hour=9, end_hour=17):
        if self.head_clock is None:
            return []
        
        optimal_times = []
        
        # Check each hour of the day
        for hour in range(24):
            all_in_range = True
            times_for_hour = []
            
            current_clock = self.head_clock
            for _ in range(self.clock_count):
                # Get current time and adjust to the test hour
                current_time = current_clock.get_current_time()
                test_time = current_time.replace(hour=hour, minute=0, second=0)
                
                times_for_hour.append({
                    'city': current_clock.city_name,
                    'time': test_time.strftime('%I:%M %p'),
                    'hour': test_time.hour
                })
                
                # Check if this hour is within business hours
                if test_time.hour < start_hour or test_time.hour >= end_hour:
                    all_in_range = False
                
                current_clock = current_clock.next_clock
            
            if all_in_range:
                optimal_times.append({
                    'reference_hour': hour,
                    'times': times_for_hour,
                    'quality': 'excellent'
                })
        
        return optimal_times
    
    def get_list_structure(self):
        if self.head_clock is None:
            return []
        
        structure = []
        current_clock = self.head_clock
        
        for i in range(self.clock_count):
            structure.append({
                'index': i,
                'city': current_clock.city_name,
                'next': current_clock.next_clock.city_name,
                'previous': current_clock.previous_clock.city_name,
                'is_head': current_clock == self.head_clock
            })
            current_clock = current_clock.next_clock
        
        return structure


# ============================================
# INITIALIZE CLOCK LIST WITH TIMEZONES
# ============================================

clock_list = CircularClockList()

clock_list.add_clock('Colombia', 'America/Bogota', 'clock_colombia.png')
clock_list.add_clock('United Kingdom', 'Europe/London', 'clock_uk.png')
clock_list.add_clock('China', 'Asia/Shanghai', 'clock_china.png')


# ============================================
# FLASK ROUTES
# ============================================

current_clock_index = 0

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/clocks')
def get_clocks():
    clocks_data = clock_list.get_all_clocks_data()
    theme = clock_list.get_dominant_theme()
    
    return jsonify({
        'clocks': clocks_data,
        'theme': theme,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/clock/current')
def get_current_clock():
    global current_clock_index
    
    current_clock = clock_list.get_clock_at_index(current_clock_index)
    if not current_clock:
        return jsonify({'error': 'No clocks available'}), 404
    
    clock_data = current_clock.get_clock_data()
    theme = 'day' if current_clock.is_daytime() else 'night'
    
    return jsonify({
        'clock': clock_data,
        'theme': theme,
        'index': current_clock_index,
        'total': clock_list.clock_count,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/clock/next')
def get_next_clock():
    global current_clock_index
    
    # Use circular linked list's next pointer
    current_clock = clock_list.get_clock_at_index(current_clock_index)
    if not current_clock:
        return jsonify({'error': 'No clocks available'}), 404
    
    # Move to next clock (demonstrates circular nature)
    current_clock_index = (current_clock_index + 1) % clock_list.clock_count
    
    next_clock = current_clock.next_clock
    clock_data = next_clock.get_clock_data()
    theme = 'day' if next_clock.is_daytime() else 'night'
    
    return jsonify({
        'clock': clock_data,
        'theme': theme,
        'index': current_clock_index,
        'total': clock_list.clock_count,
        'direction': 'next',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/clock/previous')
def get_previous_clock():
    global current_clock_index
    
    # Use circular linked list's previous pointer
    current_clock = clock_list.get_clock_at_index(current_clock_index)
    if not current_clock:
        return jsonify({'error': 'No clocks available'}), 404
    
    # Move to previous clock (demonstrates doubly-linked nature)
    current_clock_index = (current_clock_index - 1) % clock_list.clock_count
    
    previous_clock = current_clock.previous_clock
    clock_data = previous_clock.get_clock_data()
    theme = 'day' if previous_clock.is_daytime() else 'night'
    
    return jsonify({
        'clock': clock_data,
        'theme': theme,
        'index': current_clock_index,
        'total': clock_list.clock_count,
        'direction': 'previous',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/clock/update-time', methods=['POST'])
def update_clock_time():
    data = request.get_json()
    
    clock_index = data.get('index', current_clock_index)
    hours_offset = data.get('hours', 0)
    minutes_offset = data.get('minutes', 0)
    
    clock = clock_list.get_clock_at_index(clock_index)
    if not clock:
        return jsonify({'error': 'Invalid clock index'}), 400
    
    # Set the time offset for this specific node in the circular list
    clock.set_time_offset(hours=hours_offset, minutes=minutes_offset)
    
    clock_data = clock.get_clock_data()
    theme = 'day' if clock.is_daytime() else 'night'
    
    return jsonify({
        'success': True,
        'clock': clock_data,
        'theme': theme,
        'message': f'Time updated for {clock.city_name}'
    })


@app.route('/api/clock/reset-time', methods=['POST'])
def reset_clock_time():
    data = request.get_json()
    
    clock_index = data.get('index', current_clock_index)
    
    clock = clock_list.get_clock_at_index(clock_index)
    if not clock:
        return jsonify({'error': 'Invalid clock index'}), 400
    
    # Reset the time offset for this node
    clock.reset_time_offset()
    
    clock_data = clock.get_clock_data()
    theme = 'day' if clock.is_daytime() else 'night'
    
    return jsonify({
        'success': True,
        'clock': clock_data,
        'theme': theme,
        'message': f'Time reset for {clock.city_name}'
    })


@app.route('/api/compare')
def compare_timezones():
    index1 = request.args.get('clock1', type=int, default=0)
    index2 = request.args.get('clock2', type=int, default=1)
    
    comparison = clock_list.calculate_time_difference(index1, index2)
    
    if comparison:
        return jsonify(comparison)
    else:
        return jsonify({'error': 'Invalid clock indices'}), 400


@app.route('/api/meeting-times')
def get_meeting_times():
    start_hour = request.args.get('start', type=int, default=9)
    end_hour = request.args.get('end', type=int, default=17)
    
    meeting_times = clock_list.find_optimal_meeting_time(start_hour, end_hour)
    
    return jsonify({
        'optimal_times': meeting_times,
        'total_options': len(meeting_times)
    })


@app.route('/api/structure')
def get_structure():
    structure = clock_list.get_list_structure()
    
    return jsonify({
        'structure': structure,
        'total_nodes': clock_list.clock_count,
        'data_structure': 'Doubly Circular Linked List'
    })


@app.route('/api/convert')
def convert_time():
    """Convert time between different timezones"""
    from_index = request.args.get('from', type=int, default=0)
    to_index = request.args.get('to', type=int, default=1)
    hour = request.args.get('hour', type=int, default=12)
    minute = request.args.get('minute', type=int, default=0)
    
    from_clock = clock_list.get_clock_at_index(from_index)
    to_clock = clock_list.get_clock_at_index(to_index)
    
    if not from_clock or not to_clock:
        return jsonify({'error': 'Invalid clock indices'}), 400
    
    # Create a datetime in the source timezone
    now = datetime.now(from_clock.timezone)
    source_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Convert to target timezone
    target_time = source_time.astimezone(to_clock.timezone)
    
    return jsonify({
        'from_city': from_clock.city_name,
        'to_city': to_clock.city_name,
        'source_time': source_time.strftime('%I:%M %p'),
        'target_time': target_time.strftime('%I:%M %p'),
        'date_change': target_time.date() != source_time.date()
    })


if __name__ == '__main__':
    print("🕰️  Starting Enhanced Vintage Clock Application...")
    print("📍 Timezones loaded:")
    for clock_data in clock_list.get_all_clocks_data():
        print(f"   - {clock_data['city']}: {clock_data['timezone']}")
    print("\n✨ New Features:")
    print("   - Carousel Navigation (Doubly Circular Linked List)")
    print("   - Manual Time Adjustment (Modify any clock)")
    print("   - Timezone Comparison Tool")
    print("   - Meeting Time Finder")
    print("   - Circular List Visualizer")
    print("   - Time Converter")
    print("\n🌐 Server running at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000)
