x=0
if x==0:
    x=1# Save the value
    with open("x_value.txt", "w") as file:
        file.write("3")  # Store the value
# Read the value next time
with open("x_value.txt", "r") as file:
    x = int(file.read())
    print(f"x is {x}")