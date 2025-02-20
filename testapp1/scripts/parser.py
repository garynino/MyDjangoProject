
import xml.etree.ElementTree as ET

# Now import models
from models import Course, Test  # Ensure this matches your app name

"""
Parses a QTI XML file and extracts questions.
"""

tree = ET.parse(r'MyWebsite/ge78b00fbbb9de0420718b00bd11a7812.xml')
root = tree.getroot()

# Function to remove namespaces
def remove_namespace(tree):     # root of tree is parameter
    for elem in tree.iter():
        if "}" in elem.tag:  # If tag has a namespace
            elem.tag = elem.tag.split("}")[-1]  # Remove namespace

# Remove namespaces
remove_namespace(root)

# begin parsing
my_tag = 'assessment'
node = root.find(f'{my_tag}')
if node is None:
    print(f"Element '{my_tag}' not found in XML!")
else:   # if 'assessment' tag exists
    the_test_number = node.get('ident')  # get 'ident' attribute from current element
    the_course = Course.objects.first()  # Get the first available course. REMOVE AFTER TESTING IS DONE

    if the_course:  # Ensure a course exists before creating the test
        test_instance = Test.objects.create(
            course=the_course,  # Required foreign key
            title="New Test",  # You can modify this as needed
            test_number=the_test_number  # Assign 'ident' to test_number
        )
        print(f"Created new test with ID {test_instance.id} and test_number: {the_test_number}")
    else:
        print("No course found. Cannot create Test record.")

