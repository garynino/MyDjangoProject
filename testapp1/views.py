# Create your views here.
from zipfile import Path

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

    def parse_just_xml(meta_path, non_meta_path):

        print(f"processing file: {meta_path}")

        xml_file_path = meta_path
        #xml_file_path = "assessment_meta.xml"
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        remove_namespace(root)

        cover_instructions_text = root.find('.//description').text

        print(f"processing file: {non_meta_path}")

        # Path to the XML file
        xml_file_path = non_meta_path
        #xml_file_path = "ge78b00fbbb9de0420718b00bd11a7812.xml"
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
        the_test_title = node.get("title")
        test_identifier = node.get("ident")

        # Get the first available course (REMOVE AFTER TESTING)
        the_course = Course.objects.first()

        if the_course is None:
            the_course = Course.objects.create(
                course_code='CS123',
                course_name='placeholder_course',
                textbook_title='placeholder Tb title',
                textbook_author='placeholder author',
                textbook_isbn='placeholder isbn',
                textbook_link='placeholder Tb link'
            )

        if not the_course:
            return JsonResponse({"error": "No course found. Cannot create Test record."}, status=400)

        # Create a new Test record
        test_instance = Test.objects.create(
            course=the_course,
            title=the_test_title,
            test_number=test_identifier,
            cover_instructions=cover_instructions_text
        )

        for section in root.findall(".//section"):
            for item in section.findall(".//item"):        # might change to section.findall(".//item")
                # Extract 'ident' attribute
                # temp1 = item.get("ident")

                qti_metadata_fields = item.findall(".//fieldentry")

                node = item.find('presentation')
                temp_node = node.find('material')       # possibly redundant statement
                temp_node = temp_node.find(".//mattext")

                question_text_field = temp_node.text

                # node should currently be already = element w 'presentation' tag

                # For now, correct answer is simply a string, Probably need to change to a table later
                correct_answer_string = None
                answer_choices = None

                correct_answer_ident = None

                the_question_type = qti_metadata_fields[0].text
                max_points_for_question = float(qti_metadata_fields[1].text)

                #MultiChoice & TF might be able to be combined. For now, they are separate
                if the_question_type == 'multiple_choice_question':
                    #
                    node = node.find('.//response_lid')
                    answer_choices_dict = {}
                    for response_label_elem in node.findall('.//response_label'):
                        response_ident = response_label_elem.get('ident')
                        response_text = response_label_elem.find('.//mattext').text
                        answer_choices_dict[response_ident] = response_text

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            temp_node = node.find('.//varequal')
                            correct_answer_ident = temp_node.text

                elif the_question_type == 'true_false_question':
                    node = node.find('.//response_lid')
                    answer_choices = ""
                    for mattext in node.findall('.//mattext'):
                        answer_choices = answer_choices + mattext.text + "; "

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            temp_node = node.find('.//varequal')
                            correct_answer_string = temp_node.text
                elif the_question_type == 'short_answer_question':  # Fill-in-the-blank question
                    answer_choices = None

                    node = item.find('resprocessing')
                    for respcondition_elem in node.findall('.//respcondition'):
                        if respcondition_elem.get('continue') == "No":
                            #
                            correct_answer_string = ""
                            for varequal_elem in respcondition_elem.findall('.//varequal'):
                                correct_answer_string = correct_answer_string + varequal_elem.text + "; "

                elif the_question_type == 'fill_in_multiple_blanks_question':
                    print('')       # this is placeholder for code to extract info from question for table
                elif the_question_type == 'multiple_answers_question':
                    node = node.find('.//response_lid')
                    answer_choices = ""
                    for mattext in node.findall('.//mattext'):
                        answer_choices = answer_choices + mattext.text + "; "

                elif the_question_type == 'multiple_dropdowns_question':
                    print('')       # this is placeholder for code to extract info from question for table
                elif the_question_type == 'matching_question':
                    print('')       # this is placeholder for code to extract info from question for table
                elif the_question_type == 'numerical_question':
                    print('')       # this is placeholder for code to extract info from question for table
                elif the_question_type == 'calculated_question':
                    print('')       # this is placeholder for code to extract info from question for table
                elif the_question_type == 'essay_question':
                    # mostly done but may need to process feedbacks or comments

                    print('')
                elif the_question_type == 'file_upload_question':
                    # should be done but may need to process feedbacks or comments

                    print('')
                elif the_question_type == 'text_only_question':
                    #placeholder for any future changes, but 99.9% sure this is done

                    print('')

                #

                # zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz

                question_instance = Question.objects.create(
                    course=the_course,
                    question_type=the_question_type,
                    question_text=question_text_field,
                    # choices_for_question=answer_choices,
                    default_points=max_points_for_question,
                    inbedded_graphic=None,
                    # correct_answer=correct_answer_string,
                    correct_answer_graphic=None,
                    chapter_num=None
                    # z
                )

                answeroption_instance = AnswerOption.objects.create(
                    question=question_instance
                    #
                )

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

            if file_name.endswith('/'):

                temp_file_list = []

                for temp_filename in filename_list:
                    if temp_filename.startswith(f'{file_name}') and (temp_filename != file_name):
                        temp_file_list.append(temp_filename)

                if temp_file_list:
                    temp_file_list = sorted(temp_file_list)

                    assessment_meta_path = temp_file_list[0]
                    questions_file_path = temp_file_list[1]

                    with zip_ref.open(assessment_meta_path) as outer_file:
                        with zip_ref.open(questions_file_path) as inner_file:

                            outer_file.seek(0)  # Reset file pointer
                            inner_file.seek(0)

                            parse_just_xml(outer_file, inner_file)
                            #


            
    #"""

    return JsonResponse({"Success": "created Test record."}, status=555)
