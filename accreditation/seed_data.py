"""Seed reference data for the demo command and QA fixtures.

These are the canonical PACUCOA area/sub-area definitions. The live area
structure is stored in the database (AccreditationArea / AccreditationSubArea);
this module is only used to seed and reset that data.
"""

DESIRED_OUTCOMES_TITLE = 'Desired Outcomes and Other Exhibits'

AREA_SUBAREAS = {
    'area-i': {
        'code': 'Area I',
        'name': 'Philosophy and Objectives',
        'subareas': [
            {'code': '1.1', 'title': 'Statement of Mission, Vision, Goals and Core Values of the Institution'},
            {'code': '1.2', 'title': 'Statement of College/Department Mission, Vision and Objectives'},
            {'code': '1.3', 'title': 'Educational Objectives of the Program and Program Outcomes/Student Learning Outcomes'},
            {'code': '1.4', 'title': 'Awareness, Acceptance and Implementation of the Institutional Philosophy, Mission, Vision, Objectives and Program Outcomes'},
            {'code': '1.5', 'title': DESIRED_OUTCOMES_TITLE},
        ],
    },
    'area-ii': {
        'code': 'Area II',
        'name': 'Faculty',
        'subareas': [
            {'code': '2.1', 'title': 'Academic Qualifications'},
            {'code': '2.2', 'title': 'Professional Performance'},
            {'code': '2.3', 'title': 'Teaching Assignments'},
            {'code': '2.4', 'title': 'Rank, Tenure, Remuneration and Fringe Benefits'},
            {'code': '2.5', 'title': 'Faculty Development'},
            {'code': '2.6', 'title': 'Research and Publications'},
            {'code': '2.7', 'title': DESIRED_OUTCOMES_TITLE},
        ],
    },
    'area-iii': {
        'code': 'Area III',
        'name': 'Instruction',
        'subareas': [
            {'code': '3.1', 'title': 'Program of Studies'},
            {'code': '3.2', 'title': 'Co-Curricular Activities'},
            {'code': '3.3', 'title': 'Instructional Process'},
            {'code': '3.4', 'title': 'Classroom Management'},
            {'code': '3.5', 'title': 'Academic Performance of Students'},
            {'code': '3.6', 'title': 'Administrative Measures for Effective Instruction'},
            {'code': '3.7', 'title': 'Other Exhibits'},
        ],
    },
    'area-iv': {
        'code': 'Area IV',
        'name': 'Laboratories',
        'subareas': [
            {'code': '4.1', 'title': 'Facilities'},
            {'code': '4.2', 'title': 'Equipment and Supplies'},
            {'code': '4.3', 'title': 'Maintenance'},
            {'code': '4.4', 'title': 'Special Provisions'},
            {'code': '4.5', 'title': DESIRED_OUTCOMES_TITLE},
        ],
    },
    'area-v': {
        'code': 'Area V',
        'name': 'Research',
        'subareas': [
            {'code': '5.1', 'title': 'Orientation'},
            {'code': '5.2', 'title': 'Human Resources'},
            {'code': '5.3', 'title': 'Activities'},
            {'code': '5.4', 'title': 'Quality'},
            {'code': '5.5', 'title': 'Support from the Administration'},
            {'code': '5.6', 'title': 'Dissemination and Utilization'},
            {'code': '5.7', 'title': 'Ethics of Research'},
            {'code': '5.8', 'title': 'Outcomes and Other Relevant Documents'},
        ],
    },
    'area-vi': {
        'code': 'Area VI',
        'name': 'Library',
        'subareas': [
            {'code': '6.1', 'title': 'Administration'},
            {'code': '6.2', 'title': 'Human Resources'},
            {'code': '6.3', 'title': 'Collections'},
            {'code': '6.4', 'title': 'Services and Use of Library'},
            {'code': '6.5', 'title': 'Financial Support'},
            {'code': '6.6', 'title': 'Physical Facilities'},
            {'code': '6.7', 'title': 'Desired Outcomes of LIC and Other Evidences'},
        ],
    },
    'area-vii': {
        'code': 'Area VII',
        'name': 'Student Services',
        'subareas': [
            {'code': '7.1', 'title': 'Administration'},
            {'code': '7.2', 'title': 'Statement of Purpose'},
            {'code': '7.3', 'title': 'Program Design and Implementation'},
            {'code': '7.4', 'title': 'Evaluation of Support Programs'},
            {'code': '7.5', 'title': 'Outcomes of Student Services Programs'},
            {'code': '7.6', 'title': 'Other Exhibits'},
        ],
    },
    'area-viii': {
        'code': 'Area VIII',
        'name': 'SOCE',
        'subareas': [
            {'code': '8.1', 'title': 'Knowledge of the Community'},
            {'code': '8.2', 'title': 'Community Relations'},
            {'code': '8.3', 'title': 'Social Awareness and Concern'},
            {'code': '8.4', 'title': 'Community Service and Involvement'},
            {'code': '8.5', 'title': 'Desired Outcomes of Extension Programs and Other Evidences'},
        ],
    },
    'area-ix': {
        'code': 'Area IX',
        'name': 'Physical Plant and Facilities',
        'subareas': [
            {'code': '9.1', 'title': 'Site'},
            {'code': '9.2', 'title': 'Campus'},
            {'code': '9.3', 'title': 'Buildings'},
            {'code': '9.4', 'title': 'Classrooms'},
            {'code': '9.5', 'title': 'Offices and Staff Rooms'},
            {'code': '9.6', 'title': 'Building Services'},
            {'code': '9.7', 'title': 'Pictures of Physical Plant and Facilities'},
            {'code': '9.8', 'title': 'Outcomes and Other Evidences'},
        ],
    },
    'area-x': {
        'code': 'Area X',
        'name': 'Organization and Management',
        'subareas': [
            {'code': '10.1', 'title': 'Administrative Organization'},
            {'code': '10.2', 'title': 'Academic Administration'},
            {'code': '10.3', 'title': 'Student Services Administration'},
            {'code': '10.4', 'title': 'Financial/Business Administration'},
            {'code': '10.5', 'title': 'Administration of Records'},
            {'code': '10.6', 'title': 'Administrative Performance'},
            {'code': '10.7', 'title': 'Institutional Planning and Development'},
            {'code': '10.8', 'title': 'Quality Assurance'},
            {'code': '10.9', 'title': DESIRED_OUTCOMES_TITLE},
        ],
    },
    'area-xi': {
        'code': 'Area XI',
        'name': 'Employability',
        'subareas': [],
    },
}
