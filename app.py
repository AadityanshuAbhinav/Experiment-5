import os
import werkzeug
from flask import Flask, render_template, request, redirect, url_for, abort, flash, get_flashed_messages
from flask_restful import Api, Resource, reqparse, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///week7_database.sqlite3"
db = SQLAlchemy()
db.init_app(app)
api = Api(app)
app.app_context().push()

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)

class Enrollments(db.Model):
    __tablename__ = 'enrollments'
    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudent_id = db.Column(db.Integer,   db.ForeignKey("student.student_id"), nullable=False)
    ecourse_id = db.Column(db.Integer,  db.ForeignKey("course.course_id"), nullable=False)
    ECourse = db.relationship('Course')
    EStudent = db.relationship('Student')

# @app.route("/", methods=["GET", "POST"])
# def students():
#     if request.method == "GET":
#         #student = db.session.query(Student).all()
#         students = Student.query.all()
#         return render_template("index.html", students=students)

@app.route('/')
def student_details():
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/student/create', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        roll_number = request.form['roll']
        first_name = request.form['f_name']
        last_name = request.form['l_name']
        courses = request.form.getlist('courses')

        # Check if the roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll number already exists. Please choose a different one.')
            return redirect(url_for('student_details'))

        student = Student(roll_number=roll_number, first_name=first_name, last_name=last_name)
        db.session.add(student)

        for course_code in courses:
            course = Course.query.filter_by(course_code=course_code).first()
            if course:
                enrollment = Enrollments(estudent_id=student.student_id, ecourse_id=course.course_id)
                db.session.add(enrollment)

        db.session.commit()
        flash('Student added successfully')
        return redirect(url_for('student_details'))
    
    courses = Course.query.all()
    return render_template('create_student.html', courses=courses)

@app.route('/student/<int:student_id>/update', methods=['GET', 'POST'])
def update_student(student_id):
    student = Student.query.get(student_id)
    courses = Course.query.all()
    
    if not student:
        flash('Student not found')
        return redirect(url_for('student_details'))
    
    if request.method == 'POST':
        # Update student details
        student.first_name = request.form['f_name']
        student.last_name = request.form['l_name']
        db.session.commit()
        
        # Handle course enrollments
        selected_courses = request.form.getlist('courses')
        enrolled_courses = Enrollments.query.filter_by(estudent_id=student.student_id).all()
        
        for enrollment in enrolled_courses:
            if enrollment.course.course_code in selected_courses:
                selected_courses.remove(enrollment.course.course_code)
            else:
                db.session.delete(enrollment)
        
        for course_code in selected_courses:
            course = Course.query.filter_by(course_code=course_code).first()
            if course:
                enrollment = Enrollments(estudent_id=student.student_id, ecourse_id=course.course_id)
                db.session.add(enrollment)
        
        db.session.commit()
        flash('Student updated successfully')
        return redirect(url_for('student_details'))
    
    return render_template('update_student.html', student=student, courses=courses)

@app.route('/student/<int:student_id>/delete', methods=['GET'])
def delete_student(student_id):
    student = Student.query.get(student_id)
    
    if student:
        # Delete the student and associated enrollments
        enrollments = Enrollments.query.filter_by(estudent_id=student.student_id).all()
        
        for enrollment in enrollments:
            db.session.delete(enrollment)
        
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully')
    else:
        flash('Student not found')
    
    return redirect(url_for('student_details'))

@app.route('/student/<int:student_id>', methods=['GET'])
def view_student(student_id):
    student = Student.query.get(student_id)
    
    if student:
        enrollments = Enrollments.query.filter_by(estudent_id=student.student_id).all()
        return render_template('view_student.html', student=student, enrollments=enrollments)
    else:
        flash('Student not found')
        return redirect(url_for('student_details'))
    
@app.route('/student/<int:student_id>/withdraw/<int:course_id>', methods=['GET'])
def withdraw_course(student_id, course_id):
    student = student.query.get(student_id)

    if student:
        estudent_id=student_id
        ecourse_id=course_id
        enrollment = Enrollments.query.get(estudent_id, ecourse_id)
        
        if enrollment:
            db.session.delete(enrollment)
            db.session.commit()
            flash('Course withdrawn successfully')

    return redirect(url_for('student_details'))

@app.route('/courses', methods=['GET'])
def view_courses():
    courses = Course.query.all()
    return render_template('view_courses.html', courses=courses)   

@app.route('/course/create', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        course_code = request.form['code']
        course_name = request.form['c_name']
        course_description = request.form['desc']

        # Check if the course_code already exists
        existing_course = Course.query.filter_by(course_code=course_code).first()
        if existing_course:
            flash('Course code already exists. Please choose a different one.')
            return redirect(url_for('view_courses'))

        course = Course(course_code=course_code, course_name=course_name, course_description=course_description)
        db.session.add(course)

        db.session.commit()
        flash('Course added successfully')
        return redirect(url_for('courses'))
    
    return render_template('create_course.html')

@app.route('/course/<int:course_id>/update', methods=['GET', 'POST'])
def update_course(course_id):
    course = Course.query.get(course_id)
    
    if not course:
        flash('Course not found')
        return redirect(url_for('view_courses'))
    
    if request.method == 'POST':
        # Update course details
        course.course_name = request.form['c_name']
        course.course_description = request.form['desc']
        db.session.commit()
        
        flash('Course updated successfully')
        return redirect(url_for('view_courses'))
    
    return render_template('update_course.html')

@app.route('/course/<int:course_id>/delete', methods=['GET'])
def delete_course(course_id):
    course = Course.query.get(course_id)
    
    if course:
        # Delete the course and associated enrollments
        enrollments = Enrollments.query.filter_by(ecourse_id=courseourse.course_id).all()
        
        for enrollment in enrollments:
            db.session.delete(enrollment)
        
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully')
    else:
        flash('Course not found')
    
    return redirect(url_for('view_courses'))
    
class CourseResource(Resource):
    def get(self, course_id):
        course = Course.query.get(course_id)
        if course:
            return {
                'course_id': course.course_id,
                'course_name': course.course_name,
                'course_code': course.course_code,
                'course_description': course.course_description
            }, 200
        else:
            return {'message': 'Course not found'}, 404

    def put(self, course_id):
        parser = reqparse.RequestParser()
        parser.add_argument('course_name', type=str, required=True)
        parser.add_argument('course_code', type=str, required=True)
        parser.add_argument('course_description', type=str)
        args = parser.parse_args()

        course = Course.query.get(course_id)
        if course:
            course.course_name = args['course_name']
            course.course_code = args['course_code']
            course.course_description = args['course_description']
            db.session.commit()
            return {
                'course_id': course.course_id,
                'course_name': course.course_name,
                'course_code': course.course_code,
                'course_description': course.course_description
            }, 200
        else:
            return {'message': 'Course not found'}, 404

    def delete(self, course_id):
        course = Course.query.get(course_id)
        if course:
            db.session.delete(course)
            db.session.commit()
            return {'message': 'Successfully Deleted'}, 200
        else:
            return {'message': 'Course not found'}, 404

api.add_resource(CourseResource, '/api/course/<int:course_id>')

class CourseListResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('course_name', type=str, required=True, help='Course Name is required')
        parser.add_argument('course_code', type=str, required=True, help='Course Code is required')
        parser.add_argument('course_description', type=str)
        args = parser.parse_args()

        # Check if the course_code is provided
        if not args['course_code']:
            return {'error_code': 'COURSE002', 'error_message': 'Course Code is required'}, 400

        # Check if the course_code already exists
        existing_course = Course.query.filter_by(course_code=args['course_code']).first()
        if existing_course:
            return {'error_message': 'Course Code already exists'}, 409

        course = Course(course_name=args['course_name'], course_code=args['course_code'], course_description=args['course_description'])
        db.session.add(course)

        try:
            db.session.commit()
            return {
                'course_id': course.course_id,
                'course_name': course.course_name,
                'course_code': course.course_code,
                'course_description': course.course_description
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'error_code': 'COURSE001', 'error_message': 'Course Name is required'}, 400

api.add_resource(CourseListResource, '/api/course')

class StudentResource(Resource):
    def get(self, student_id):
        student = Student.query.get(student_id)
        if student:
            return {
                'student_id': student.student_id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'roll_number': student.roll_number,            
            }, 200
        else:
            return {'message': 'Student not found'}, 404
        
    def put(self, student_id):
        parser = reqparse.RequestParser()
        parser.add_argument('first_name', type=str, required=True)
        parser.add_argument('last_name', type=str, required=True)
        parser.add_argument('roll_number', type=str)
        args = parser.parse_args()

        student = Student.query.get(student_id)
        if student:
            student.first_name = args['first_name']
            student.last_name = args['last_name']
            student.roll_number = args['roll_number']
            db.session.commit()
            return {
                'student_id': student.student_id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'roll_number': student.roll_number
            }, 200
        else:
            return {'message': 'Student not found'}, 404
        
    def delete(self, student_id):
        student = Student.query.get(student_id)
        if student:
            db.session.delete(student)
            db.session.commit()
            return {'message': 'Successfully Deleted'}, 200
        else:
            return {'message': 'Student not found'}, 404

api.add_resource(StudentResource, '/api/student/<int:student_id>')

class StudentListResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('first_name', type=str, required=True, help='First Name is required')
        parser.add_argument('last_name', type=str, required=True)
        parser.add_argument('roll_number', type=str, required=True, help='Roll Number is required')
        args = parser.parse_args()

        # Check if the roll_number is provided
        if not args['roll_number']:
            return {'error_code': 'STUDENT001', 'error_message': 'Roll Number is required'}, 400

        # Check if the roll_number already exists
        existing_student = Student.query.filter_by(roll_number=args['roll_number']).first()
        if existing_student:
            return {'error_message': 'Roll Number already exists'}, 409

        student = Student(first_name=args['first_name'], last_name=args['last_name'], roll_number=args['roll_number'])
        db.session.add(student)

        try:
            db.session.commit()
            return {
                'student_id': student.student_id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'roll_number': student.roll_number
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'error_code': 'STUDENT002', 'error_message': 'First Name is required'}, 400

api.add_resource(StudentListResource, '/api/student')

class EnrollmentResource(Resource):
    def get(self, student_id):
        enrollments = Enrollments.query.filter_by(student_id=student_id).all()
        if enrollments:
            enrollment_list = [{
                'enrollment_id': enrollment.enrollment_id,
                'student_id': enrollment.student_id,
                'course_id': enrollment.course_id,
            } for enrollment in enrollments]
            return enrollment_list
        else:
            return {'message': 'Student is not enrolled in any course'}, 404


    def post(self, student_id):
        parser = reqparse.RequestParser()
        parser.add_argument('course_id', type=int, required=True)

        args = parser.parse_args()

        # Check if the course exists
        existing_course = Course.query.get(args['course_id'])
        if not existing_course:
            return {'error_code': 'ENROLLMENT001', 'error_message': 'Course does not exist'}, 400

        # Check if the student exists
        existing_student = Student.query.get(student_id)
        if not existing_student:
            return {'error_code': 'ENROLLMENT002', 'error_message': 'Student does not exist'}, 400
        
        enrollment = Enrollments(student_id=student_id, course_id=args['course_id'])
        db.session.add(enrollment)

        try:
            db.session.commit()
            return {
                'enrollment_id': enrollment.enrollment_id,
                'student_id': enrollment.student_id,
                'course_id': enrollment.course_id,
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'error_code': 'ENROLLMENT003', 'error_message': 'Enrollment failed'}, 500

api.add_resource(EnrollmentResource, '/api/student/<int:student_id>/course')

class EnrollmentListResource(Resource):
    def delete(self, student_id, course_id):
        enrollment = Enrollments.query.filter_by(student_id=student_id, course_id=course_id).first()
        if enrollment:
            db.session.delete(enrollment)
            db.session.commit()
            return {'message': 'Successfully deleted'}, 200
        else:
            return {'message': 'Enrollment for the student not found'}, 404

api.add_resource(EnrollmentListResource, '/api/student/<int:student_id>/course/<int:course_id>')

if __name__ == '__main__':
  # Run the Flask app
  app.run(debug=False,host='0.0.0.0')
