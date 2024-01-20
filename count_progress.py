import time


if __name__ == '__main__':
    while(True):
        with open("output.csv") as wo:
            rows = 0;
            for row in wo:
                rows+=1;
            
            print(f"Number of rows is: {rows}" )
        
        time.sleep(1*60)
    
