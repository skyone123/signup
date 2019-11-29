# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ser_user
   Description :
   Author :       jusk?
   date：          2019/9/15
-------------------------------------------------
   Change Activity:
                   2019/9/15:
-------------------------------------------------
"""
import jwt
from ..models import UserProfile, Menu
from rest_framework.generics import ListAPIView
from common.custom import CommonPagination, RbacPermission
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.hashers import check_password


from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from ..serializers.ser_serializers import UserListSerializer, UserCreateSerializer, \
    UserModifySerializer, UserInfoListSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication


from signup.code import *
from users.models import Menu
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from signup.basic import XopsResponse
from signup.settings import SECRET_KEY
from ..serializers.menu_serializer import MenuSerializer


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

class UserAuthView(APIView):
    '''
    用户认证获取token
    '''
    def post(self, request):
        """
        post:
        发送信息到指定人员邮箱
        参数列表：

            username：用户名
            password：密码

        """
        username = request.data.get('username')
        password = request.data.get('password')
        print(username)
        print(password)
        user = authenticate(username=username, password=password)
        if user:
            payload = jwt_payload_handler(user)
            return XopsResponse({'token': jwt.encode(payload, SECRET_KEY),'username':username}, status=OK,)
        else:
            return XopsResponse('用户名或密码错误!', status=BAD)

from  rest_framework.versioning import BaseVersioning,QueryParameterVersioning,URLPathVersioning
class Myversion(BaseVersioning):
    def determine_version(self, request, *args, **kwargs):
        myversion=request.query_params.get('version')
        print(myversion)
        return myversion

from common.custom import DepartmentSerializer
class UserInfoView(APIView):
    '''
    获取当前用户信息和权限
    '''

    versioning_class = QueryParameterVersioning  # 添加版本
    @classmethod
    def get_permission_from_role(self, request):
        try:
            if request.user:
                perms_list = []
                for item in request.user.roles.values('permissions__method').distinct():
                    perms_list.append(item['permissions__method'])
                return perms_list
        except AttributeError:
            return None

    @classmethod
    def get_department_from_organization(self, request):
        try:
            if request.user:
                org = request.user.department.values(
                        "id",
                        "name",
                ).distinct()
                print(org)
                serializer = DepartmentSerializer(org, many=True)
                return serializer.data
        except AttributeError:
            return None

    def get(self, request):
        """
        get:
        发送信息到指定人员邮箱
        参数列表：

            id：用户id
            username：用户名
            avatar：头像接口
            email：邮件
            is_active：是否激活
            createTime：创建时间
            position: 职位
            roles：角色

        """
        # print("dd"+str(request.version))
        # print(request._request)
        # request._full_data = "dd"
        # print(request.data)
        # print(request.negotiator)
        # print(request.data)
        # print(request.FILES)
        # url = request.versioning_scheme.reverse(viewname='user_info', request=request)
        # print(url)
        if request.user.id is not None:
            perms = self.get_permission_from_role(request)
            org = self.get_department_from_organization(request)

            data = {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'is_active': request.user.is_active,
                'createTime':request.user.date_joined,
                'department':org,
                'position': request.user.position,
                'roles': perms,
            }
            return XopsResponse(data, status=OK)
        else:
            return XopsResponse('请登录后访问!', status=FORBIDDEN)



class UserBuildMenuView(APIView):
    '''
    绑定当前用户菜单信息
    '''
    def get_menu_from_role(self, request):
        if request.user:
            menu_dict = {}
            menus = request.user.roles.values(
                'menus__id',
                'menus__name',
                'menus__path',
                'menus__is_frame',
                'menus__is_show',
                'menus__component',
                'menus__icon',
                'menus__sort',
                'menus__pid'
            ).distinct()
            for item in menus:
                if item['menus__pid'] is None:
                    if item['menus__is_frame']:
                        # 判断是否外部链接
                        top_menu = {
                            'id': item['menus__id'],
                            'path': item['menus__path'],
                            'component': 'Layout',
                            'children': [{
                                'path': item['menus__path'],
                                'meta': {
                                    'title': item['menus__name'],
                                    'icon': item['menus__icon']
                                }
                            }],
                            'pid': item['menus__pid'],
                            'sort': item['menus__sort']
                        }
                    else:
                        top_menu = {
                            'id': item['menus__id'],
                            'name': item['menus__name'],
                            'path': '/' + item['menus__path'],
                            'redirect': 'noredirect',
                            'component': 'Layout',
                            'alwaysShow': True,
                            'meta': {
                                'title': item['menus__name'],
                                'icon': item['menus__icon']
                            },
                            'pid': item['menus__pid'],
                            'sort': item['menus__sort'],
                            'children': []
                        }
                    menu_dict[item['menus__id']] = top_menu
                else:
                    if item['menus__is_frame']:
                        children_menu = {
                            'id': item['menus__id'],
                            'name': item['menus__name'],
                            'path': item['menus__path'],
                            'component': 'Layout',
                            'meta': {
                                'title': item['menus__name'],
                                'icon': item['menus__icon'],
                            },
                            'pid': item['menus__pid'],
                            'sort': item['menus__sort']
                        }
                    elif item['menus__is_show']:
                        children_menu = {
                            'id': item['menus__id'],
                            'name': item['menus__name'],
                            'path': item['menus__path'],
                            'component': item['menus__component'],
                            'meta': {
                                'title': item['menus__name'],
                                'icon': item['menus__icon'],
                            },
                            'pid': item['menus__pid'],
                            'sort': item['menus__sort']
                        }
                    else:
                        children_menu = {
                            'id': item['menus__id'],
                            'name': item['menus__name'],
                            'path': item['menus__path'],
                            'component': item['menus__component'],
                            'meta': {
                                'title': item['menus__name'],
                                'noCache': True,
                            },
                            'hidden': True,
                            'pid': item['menus__pid'],
                            'sort': item['menus__sort']
                        }
                    menu_dict[item['menus__id']] = children_menu
            return menu_dict

    def get_all_menu_dict(self):
        '''
        获取所有菜单数据，重组结构
        '''
        menus = Menu.objects.all()
        serializer = MenuSerializer(menus, many=True)
        tree_dict = {}
        for item in serializer.data:
            if item['pid'] is None:
                if item['is_frame']:
                    # 判断是否外部链接
                    top_menu = {
                        'id': item['id'],
                        'path': item['path'],
                        'component': 'Layout',
                        'children': [{
                            'path': item['path'],
                            'meta': {
                                'title': item['name'],
                                'icon': item['icon']
                            }
                        }],
                        'pid': item['pid'],
                        'sort': item['sort']
                    }
                else:
                    top_menu = {
                        'id': item['id'],
                        'name': item['name'],
                        'path': '/' + item['path'],
                        'redirect': 'noredirect',
                        'component': 'Layout',
                        'alwaysShow': True,
                        'meta': {
                            'title': item['name'],
                            'icon': item['icon']
                        },
                        'pid': item['pid'],
                        'sort': item['sort'],
                        'children': []
                    }
                tree_dict[item['id']] = top_menu
            else:
                if item['is_frame']:
                    children_menu = {
                        'id': item['id'],
                        'name': item['name'],
                        'path': item['path'],
                        'component': 'Layout',
                        'meta': {
                            'title': item['name'],
                            'icon': item['icon'],
                        },
                        'pid': item['pid'],
                        'sort': item['sort']
                    }
                elif item['is_show']:
                    children_menu = {
                        'id': item['id'],
                        'name': item['name'],
                        'path': item['path'],
                        'component': item['component'],
                        'meta': {
                            'title': item['name'],
                            'icon': item['icon'],
                        },
                        'pid': item['pid'],
                        'sort': item['sort']
                    }
                else:
                    children_menu = {
                        'id': item['id'],
                        'name': item['name'],
                        'path': item['path'],
                        'component': item['component'],
                        'meta': {
                            'title': item['name'],
                            'noCache': True,
                        },
                        'hidden': True,
                        'pid': item['pid'],
                        'sort': item['sort']
                    }
                tree_dict[item['id']] = children_menu
        return tree_dict

    def get_all_menus(self, request):
        perms = UserInfoView.get_permission_from_role(request)
        tree_data = []
        if 'admin' in perms or request.user.is_superuser:
            tree_dict = self.get_all_menu_dict()
        else:
            tree_dict = self.get_menu_from_role(request)
        for i in tree_dict:
            if tree_dict[i]['pid']:
                pid = tree_dict[i]['pid']
                parent = tree_dict[pid]
                parent.setdefault('redirect', 'noredirect')
                parent.setdefault('alwaysShow', True)
                parent.setdefault('children', []).append(tree_dict[i])
                # parent['children'] = sorted(parent['children'], key=itemgetter('sort'))
            else:
                tree_data.append(tree_dict[i])
        return tree_data

    def get(self, request):
        """
        get:
        获取所有菜单数据，重组结构
        """
        if request.user.id is not None:
            menu_data = self.get_all_menus(request)
            return XopsResponse(menu_data, status=OK)
        else:
            return XopsResponse('请登录后访问!',status=FORBIDDEN)



class UserViewSet(ModelViewSet):
    '''
    用户管理：增删改查

    list:
        获取所有用户信息+id获取某人具体信息
    create:
        添加用户信息
    delete:
        删除用户信息
    update:
        修改用户信息
    '''
    perms_map = ({'*': 'admin'}, {'*': 'user_all'}, {'get': 'user_list'}, {'post': 'user_create'}, {'put': 'user_edit'},
                 {'delete': 'user_delete'})
    queryset = UserProfile.objects.all()
    serializer_class = UserListSerializer
    pagination_class = CommonPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('is_active',)
    search_fields = ('username', 'name', 'mobile', 'email')
    ordering_fields = ('id',)
    authentication_classes = (JSONWebTokenAuthentication,SessionAuthentication)
    # permission_classes = (RbacPermission,)

    def get_serializer_class(self):
        # 根据请求类型动态变更serializer
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserModifySerializer

    def create(self, request, *args, **kwargs):
        # 创建用户默认添加密码
        data=request.data.copy()
        print(data)
        data['password'] = '123456'
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return XopsResponse(serializer.data, status=CREATED, headers=headers)


    def destroy(self, request, *args, **kwargs):
        # 删除用户时删除其他表关联的用户
        instance = self.get_object()
        id = str(kwargs['pk'])
        # projects = Project.objects.filter(
        #     Q(user_id__icontains=id + ',') | Q(user_id__in=id) | Q(user_id__endswith=',' + id)).values()
        # if projects:
        #     for project in projects:
        #         user_id = project['user_id'].split(',')
        #         user_id.remove(id)
        #         user_id = ','.join(user_id)
                # Project.objects.filter(id=project['id']).update(user_id=user_id)
        # ConnectionInfo.objects.filter(uid_id=id).delete()
        self.perform_destroy(instance)
        return XopsResponse(status=NO_CONTENT)

    # @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
    #         url_path='change-passwd', url_name='change-passwd')
    def set_password(self, request, pk=None):
        perms = UserInfoView.get_permission_from_role(request)
        user = UserProfile.objects.get(id=pk)
        if 'admin' in perms or 'user_all' in perms or request.user.is_superuser:
            new_password1 = request.data['new_password1']
            new_password2 = request.data['new_password2']
            if new_password1 == new_password2:
                user.set_password(new_password2)
                user.save()
                return XopsResponse('密码修改成功!')
            else:
                return XopsResponse('新密码两次输入不一致!', status=status.HTTP_400_BAD_REQUEST)
        else:
            old_password = request.data['old_password']
            if check_password(old_password, user.password):
                new_password1 = request.data['new_password1']
                new_password2 = request.data['new_password2']
                if new_password1 == new_password2:
                    user.set_password(new_password2)
                    user.save()
                    return XopsResponse('密码修改成功!')
                else:
                    return XopsResponse('新密码两次输入不一致!', status=status.HTTP_400_BAD_REQUEST)
            else:
                return XopsResponse('旧密码错误!', status=status.HTTP_400_BAD_REQUEST)


class UserListView(ListAPIView):
    '''
    list:
    用户管理
        获取所有用户信息
    '''
    queryset = UserProfile.objects.all()
    serializer_class = UserInfoListSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_fields = ('name',)
    ordering_fields = ('id',)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)