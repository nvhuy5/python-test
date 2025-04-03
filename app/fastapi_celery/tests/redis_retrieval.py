import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6380, db=0)

# Using SCAN to get keys in a non-blocking way
cursor = 0
keys = []

while cursor != 0:
    cursor, partial_keys = r.scan(cursor=cursor, match='*')  # Use a pattern like * to match all keys
    keys.extend(partial_keys)

# Print all keys
print("All keys:", [key.decode('utf-8') for key in keys])


for key in [key.decode('utf-8') for key in keys]:
    # Retrieve a value by key
    value = r.get(key)

    if value:
        print(f"Value: {value.decode('utf-8')}")
    else:
        print("Key not found")