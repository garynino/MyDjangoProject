import xml.etree.ElementTree as ET

def parse_qti(qti_file_path):
    """
    Parses a QTI XML file and extracts questions.
    """
    tree = ET.parse(qti_file_path)
    root = tree.getroot()

    node = root.find('assessment')
    attrib_dict = node.attrib
    print(node.attrib)





    return