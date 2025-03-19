import sys

# ฟังก์ชันสำหรับอ่านเวลาใน config_time.txt พร้อม error handling
def read_config_time(file_path='config_time.txt'):
    config = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Skip empty lines or lines that don't contain '='
                if '=' not in line or not line.strip():
                    continue
                
                # Split the line into key and value and strip spaces
                key_value = line.strip().split('=')

                # Ensure there are exactly two parts (key and value)
                if len(key_value) != 2:
                    print(f"Skipping invalid line: {line.strip()}")
                    continue

                key, value = key_value

                if key in ['scrape_times', 'delete_times']:
                    # แยกเวลาและตรวจสอบความถูกต้องของรูปแบบเวลา
                    try:
                        config[key] = [(int(t.split(':')[0]), int(t.split(':')[1])) for t in value.split(',')]
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing time values in line: {line.strip()} - {e}")
                        continue
                else:
                    try:
                        config[key] = int(value)
                    except ValueError as e:
                        print(f"Error parsing integer values in line: {line.strip()} - {e}")
                        continue
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)  
    return config

