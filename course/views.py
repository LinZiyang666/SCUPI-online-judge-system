from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from .models import Message,MessageRead

class CourseSerializer(serializers.Serializer):
    course_name = serializers.CharField(required = True, max_length=100)
    students_list = serializers.ListField(child = serializers.CharField(max_length = 20))
#序列化器还有预留位

class GroupSerializer(serializers.Serializer):
    course_name = serializers.CharField(source='name', max_length=100)
#序列化器还有预留位  

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        fields = ['username', 'first_name']

class MessageSerializer(serializers.Serializer):
    level=serializers.CharField(max_length=10)
    title=serializers.CharField(max_length=255)
    content=serializers.CharField()
    receiver=serializers.ListField(child=serializers.CharField(max_length = 20))
    receive_group=serializers.CharField()


    
class CourseView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        this_user = User.objects.filter(username=request.session.get('username')).first()
        if this_user.groups.filter(name="administrator").exists():
            #只有管理员能创建班级
            serializer = CourseSerializer(data=request.data)
            if serializer.is_valid():
                course = serializer.validated_data
                course_name = course['course_name']
                students_list = course['students_list']
                
                if Group.objects.filter(name=course_name).exists():
                    return Response({"error": "Invalid course name"}, status=status.HTTP_400_BAD_REQUEST)
                new_course, created = Group.objects.get_or_create(name=course_name)
                for student in students_list:
                    new_student = User.objects.filter(username=student).first()
                    if new_student is not None:
                        new_course.user_set.add(new_student)
                    else:
                        new_course.delete()
                        return Response({"error": "fail to create this course"}, status=status.HTTP_400_BAD_REQUEST)  
                        
                return Response({"success": "Course created successfully"}, status=status.HTTP_200_OK)
                
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            
        else:
            return Response({"error": "You don't have permission to create course"}, status=status.HTTP_403_FORBIDDEN)
    
    def delete(self, request, *args, **kwargs):
        this_user = User.objects.filter(username=request.session.get('username')).first()        
        if this_user.groups.filter(name="administrator").exists():
            #只有管理员可以删除课程
            course_name = request.data.get('course_name')
            if course_name is not None and course_name != 'teacher' and course_name != 'student' and course_name != 'administrator':
                try:   
                    course = Group.objects.get(name=course_name)
                    course.delete()
                    return Response({"success": "Group deleted successfully"}, status=status.HTTP_200_OK)
                except Group.DoesNotExist:
                    return Response({"error": "Group not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({"error": "course name error"}, status=status.HTTP_400_BAD_REQUEST)     
                       
        else:
            return Response({"error": "You don't have permission to delete course"}, status=status.HTTP_403_FORBIDDEN)
            
    def put(self, request, *args, **kwargs):
        this_user = User.objects.filter(username=request.session.get('username')).first()
        if this_user.groups.filter(name="administrator").exists():
            #只有管理员能编辑班级成员
            serializer = CourseSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    course = serializer.validated_data
                    course_name = kwargs.get('coursename')
                    students_list = course['students_list']
                    
                    if not Group.objects.filter(name=course_name).exists():
                        return Response({"error": "Invalid course not exist"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    course = Group.objects.get(name=course_name)
                    old_student = course.user_set.values_list('username', flat=True)
                    
                    students_to_add = list(set(students_list) - set(old_student))
                    students_to_delete = list(set(old_student) - set(students_list))
                    
                    print("add:",students_to_add)
                    print("delete:",students_to_delete)
                    
                    for student in students_to_add:
                        if not User.objects.filter(username = student):
                            return Response({"success": "Students to add not exist"}, status=status.HTTP_400_BAD_REQUEST)
                        
                    for student in students_to_add:
                        user = User.objects.get(username = str(student))
                        course.user_set.add(user)
                            
                    for student in students_to_delete:
                        print(student)
                        user = User.objects.get(username = str(student))
                        course.user_set.remove(user)
                        
                    return Response({"success": "Group update successfully"}, status=status.HTTP_200_OK)    
                except:
                    return Response({"error": "Students to add not exist"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            
        else:
            return Response({"error": "You don't have permission to create course"}, status=status.HTTP_403_FORBIDDEN)       
    
    def get(self, request, *args, **kwargs):
        course_name = kwargs.get('coursename')
        if course_name is not None:
            this_user = User.objects.get(username=request.session.get('username'))
            try:
                course = Group.objects.get(name = course_name)
            except: 
                return Response({"error": "course not exist"}, status=status.HTTP_400_BAD_REQUEST)       
            if course is None or (not this_user.groups.filter(name=course_name).exists() and request.session.get('role') != 'administrator'):
                #课程不存在或（用户不在课程中且用户不是管理员）
                return Response({"error": "You don't have permission to visit this course"}, status=status.HTTP_403_FORBIDDEN)

            course = Group.objects.get(name=course_name)
            students_list = course.user_set.values_list('username', flat = True)
            students = User.objects.filter(username__in=students_list)
            serializer = UserSerializers(students, many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
            
        elif request.session.get('role') == 'administrator':
            #管理员有权查看所有课程
            course_name = Group.objects.all()
            course_name = course_name.exclude(name = 'administrator')
            course_name = course_name.exclude(name = 'teacher')
            course_name = course_name.exclude(name = 'student')
            serializer = GroupSerializer(course_name, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            this_user =  User.objects.get(username=request.session.get('username'))
            course_name = this_user.groups.all()
            course_name = course_name.exclude(name = 'administrator')
            course_name = course_name.exclude(name = 'teacher')
            course_name = course_name.exclude(name = 'student')
            serializer = GroupSerializer(course_name, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class MessageView(APIView):
    permission_classes = [IsAuthenticated]



    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)

        if serializer.is_valid():
            if not all(
                    User.objects.filter(username=name).exists() for name in serializer.validated_data['receiver']):
                return Response({'error': 'user not exist'}, status=status.HTTP_404_NOT_FOUND)
            try:
                this_user = User.objects.get(username=request.session.get('username'))
                message = Message()
                message.level = serializer.validated_data['level']
                message.title = serializer.validated_data['title']
                message.content = serializer.validated_data['content']
                message.sender = this_user
                message.save()
            except:
                return Response({'error': 'message save error'}, status=status.HTTP_404_NOT_FOUND)
            for receiver_name in serializer.validated_data['receiver']:
                try:
                    receiver = User.objects.get(username=receiver_name)
                    message_read = MessageRead()
                    message_read.message = message
                    message_read.user = receiver
                    message_read.save()
                except:
                    return Response({'error': 'receiver save error'}, status=status.HTTP_404_NOT_FOUND)

            return Response(request.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        message_id=kwargs.get('message_id')
        this_message=Message.objects.get(id=message_id)
        try:
            this_message.update(level=kwargs.get('level'),title=kwargs.get('title'),content=kwargs.get('content'))
        except:
            return Response({'error': 'message save error'}, status=status.HTTP_404_NOT_FOUND)
        message_read=MessageRead.objects.filter(message=this_message)

        for receiver_read in message_read:
            receiver_read.delete()
        for receiver_name in serializer.validated_data['receiver']:
            try:
                receiver = User.objects.get(username=receiver_name)
                message_read = MessageRead()
                message_read.message = this_message
                message_read.user = receiver
                message_read.save()
            except:
                return Response({'error': 'receiver save error'}, status=status.HTTP_404_NOT_FOUND)
        return Response(request.data, status=status.HTTP_200_OK)
    def delete(self, request, *args, **kwargs):
        message_id=kwargs.get('message_id')
        this_message=Message.objects.get(id=message_id)
        try:
            this_message.delete()
        except:
            return Response({'error': 'message not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(request.data, status=status.HTTP_200_OK)