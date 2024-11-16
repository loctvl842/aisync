from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor() as executor:
    executor.submit(lambda: print("Hello"))
