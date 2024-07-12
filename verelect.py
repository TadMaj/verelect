import sys
import elements
def run_all():
    elements.form_element_model()

def main():
    # Get all arguments
    args = sys.argv[1:]
    
    if len(args) == 0:
        run_all()
        return

    for arg in args:
        match arg:
            case "element":
                elements.form_element_model()
            case _:
                print(f"Invalid argument: {arg}")

if __name__ == "__main__":
    main()
