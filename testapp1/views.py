# Create your views here.
from django.shortcuts import render

from django.http import HttpResponse

from testapp1.models import *

import xml.etree.ElementTree as ET
import html
import re

import os
import zipfile
from django.conf import settings
from django.core.files.storage import default_storage

from django.http import JsonResponse

def hello_world(request):
    return HttpResponse("Hello, world!")


def parse_qti_xml(request):
    """
    Parses a QTI XML file and saves extracted data to the database.
    """

    # Function to remove namespaces
    def remove_namespace(given_tree):
        for elem in given_tree.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}")[-1]

    zip_file = None
    if request.method == "POST" and request.FILES:
        zip_file = list(request.FILES.values())[0]  # Convert files to list, then get first element
        print("File uploaded:", zip_file.name)
    else:
        print("No file uploaded to website.")
    """
    if zip_file == None:
        return JsonResponse({"message": "No file uploaded to website."})
    """

    #"""
    path_to_zip_file = 'qti sample w one quiz-slash-test w all typesofquestions.zip'
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        # List all files inside the zip file
        filename_list = zip_ref.namelist()

        for file_name in filename_list:

            if file_name.is_dir():
                print(f'{file_name}')

            
            #with zip_ref.open(file_name) as file:
            
    #"""
    try:

        xml_file_path = "assessment_meta.xml"
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        remove_namespace(root)

        raw_html = root.find('.//description').text
        # Remove all HTML tags using regex
        clean_text = re.sub(r"<[^>]+>", " ", raw_html)  # Replace tags with a space
        # Decode HTML entities (e.g., &nbsp; → " ", &amp; → "&")
        clean_text = html.unescape(clean_text)
        # Normalize spaces
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        cover_instructions_text = clean_text


        # Path to the XML file
        xml_file_path = "ge78b00fbbb9de0420718b00bd11a7812.xml"
        # Load XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        namespace = {"ns": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2"}

        # Remove namespaces
        remove_namespace(root)

        # Find the 'assessment' element
        my_tag = "assessment"
        node = root.find(my_tag)

        if node is None:
            return JsonResponse({"error": f"Element '{my_tag}' not found in XML!"}, status=400)

        # Extract 'ident' and 'title' attribute
        temp2 = node.get("title")
        temp3 = node.get("ident")


        # Get the first available course (REMOVE AFTER TESTING)
        the_course = Course.objects.first()

        if not the_course:
            return JsonResponse({"error": "No course found. Cannot create Test record."}, status=400)

        # Create a new Test record
        test_instance = Test.objects.create(
            course=the_course,
            title=f"{temp2}",
            test_number=temp3,
            cover_instructions=cover_instructions_text
        )

        for section in root.findall(".//section"):
            for item in root.findall(".//item"):
                # Extract 'ident' attribute
                #temp1 = item.get("ident")

                qti_metadata_fields = item.findall(".//fieldentry")

                node = item.find('presentation')
                temp_node = node.find('material')
                temp_node = node.find(".//mattext")

                question_text_field = html.unescape(temp_node.text)
                # Remove <div> tags using regex
                question_text_field = re.sub(r"</?div>", "", question_text_field)

                # node should currently be already = element w 'presentation' tag
                node = node.find('.//response_lid')
                answer_choices = ""
                for mattext in node.findall('.//mattext'):
                    answer_choices = answer_choices + mattext.text + "; "

                #

                #zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz

                question_instance = Question.objects.create(
                    course=the_course,
                    question_type=qti_metadata_fields[0].text,
                    question_text=question_text_field,
                    choices_for_question=answer_choices,
                    default_points=float(qti_metadata_fields[1].text),
                    inbedded_graphic=None,
                    correct_answer=None,
                    correct_answer_graphic=None
                    #z
                )

        return JsonResponse({"message": "Created new record"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
