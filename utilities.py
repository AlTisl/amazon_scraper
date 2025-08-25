from random import uniform
from time import sleep    

def random_delay(min: int, max: int) -> None:
    assert min >=0 and max > min
    delay = uniform(min, max)
    sleep(delay)