from urllib.parse import urljoin
from django.test import Client, TestCase
from django.urls import reverse
from .models import Post, Group, User, Follow, Comment
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.core.cache import cache
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image



class TestUserScript(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.user = User.objects.create_user(
            username="sarah", 
            email="connor.s@skynet.com"
        )
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(
            username="follower", 
            email="connor@sky.com"
        )
        self.user_following = User.objects.create_user(
            username="following", 
            email="following@mail.ru"
        )
        self.client_auth_following.force_login(self.user_following)
        self.client_auth.force_login(self.user)
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="testgroup",
            description="Описание тестовой группы",
        )
        cache.clear()
        
    def test_profile(self):
        """После регистрации пользователя создается 
        его персональная страница (profile)"""
        response = self.client_auth.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(
                response.context["author"].username, self.user.username
        )

    def test_new_post(self):
        """Авторизованный пользователь может опубликовать пост (new)"""
        response = self.client_auth.post(reverse('new_post'),
                                     data={'text': 'text',
                                           'group': self.group.id,
                                           'author': self.user},
                                     follow=True)
        self.assertEqual(response.status_code, 200)
        posts_new = Post.objects.all()
        self.assertEqual(posts_new.first().text, 'text')
        self.assertEqual(posts_new.count(), 1)
        self.assertEqual(posts_new.first().author, self.user)
        self.assertEqual(posts_new.first().group, self.group)

    def test_no_new_post(self):
        """Неавторизованный посетитель не может опубликовать пост 
        (его редиректит на страницу входа)"""
        post = self.client.post(
            reverse("new_post"), {"text": "test", "group": self.group.id}
        )
        self.assertFalse(Post.objects.filter(
            text="test").exists())
        response = self.client.get(reverse("new_post"), follow=False)
        self.assertEqual(response.status_code, 302)

    def _check_post(self, url, group, text, author):  
        response = self.client_auth.get(url)  
        if 'paginator' in response.context:  
            posts = response.context['paginator'].object_list[0]  
        else:  
            posts = response.context["post"]  
        self.assertEqual(posts.text, text)  
        self.assertEqual(posts.author, author)  
        self.assertEqual(posts.group, group)  
 
    def test_post_show(self): 
        post = Post.objects.create(text='text', author=self.user, 
                                   group=self.group) 
        for url in ( 
                reverse("index"), 
                reverse("profile", kwargs={"username": self.user.username} 
                        ), 
                reverse("post", kwargs={ 
                    "username": self.user.username, 
                    "post_id": post.id} 
                        ) 
        ): 
            self._check_post(url, self.group, post.text, self.user) 

    def test_post_edit(self):
        post = Post.objects.create(text='text', author=self.user,
                                   group=self.group)
        new_group = Group.objects.create(
            title="Bank",
            slug="ank"
        )
        post_text = "edit_text"
        response = self.client_auth.post(
            reverse(
                "post_edit",
                kwargs={
                    "username": self.user.username,
                    "post_id": post.id,
                }
            ), follow=True,
            data={'text': post_text, 'group': new_group.id}
        )
        self.assertEqual(response.status_code, 200)
        posts_new = Post.objects.first()
        for url in (
                reverse("index"),
                reverse("profile", kwargs={"username": self.user.username}
                ),
                reverse("post", kwargs={
                    "username": self.user.username,
                    "post_id": post.id}
                        ),
                reverse('group', kwargs={'slug': new_group.slug})
        ):
            self._check_post(url, new_group, post_text, self.user)
    
    def test_cache(self):
        self.client_auth.post(reverse('new_post'),
                              data={'text': 'text',
                                    'group': self.group.id,
                                    'author': self.user},
                              follow=True)
        posts_new = Post.objects.all()
        response = self.client_auth.get(reverse('index'))
        text = Post.objects.filter(text='text')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, text)
        cache.clear()
        response = self.client_auth.get(reverse('index'))
        text = 'text'
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, text) 

    def test_follow_and_unfollow(self):
        author = self.user_following
        self.client_auth.get(reverse('profile_follow',
                                    kwargs={
                                         'username': author.username
                                    }
                                ),
        )
        follow = Follow.objects.all()
        self.assertEqual(len(follow), 1)
        self.assertEqual(follow.first().author, author)
        self.client_auth.get(reverse('profile_unfollow',
                                    kwargs={
                                            'username': author.username
                                    }
                                ),
        )
        follow = Follow.objects.all()
        self.assertEqual(len(follow), 0)

    def test_append_post_in_follow_index(self):
        author = self.user_following
        post = Post.objects.create(
            text="text",
            author=author
        )
        self.client_auth.get(
            reverse('profile_follow',
                    kwargs={
                            'username': author.username
                }
            ),
        )
        response = self.client_auth.get(reverse('follow_index'))
        self.assertEqual(response.status_code, 200)
        current_post = response.context['paginator'].object_list[0]
        self.assertEqual(
            len(response.context['paginator'].object_list), 1
        )
        self.assertEqual(current_post.author, post.author)
        self.assertEqual(current_post.text, post.text)

    def test_image(self):
        """Проверка загрузки графического файла"""
        file = BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        img = SimpleUploadedFile(
            file.name, file.read(), content_type='image/png'
        )
        post = Post.objects.create(
            text="проверка изображения",
            author=self.user,
            group=self.group,
            image=img
        )
        for url in (
                reverse('index'),
                reverse('profile', kwargs={
                                           'username': self.user.username
                                           }
                ),
                reverse('group', kwargs={'slug': self.group.slug}),
                reverse(
                    'post', kwargs={
                    "username": self.user.username, 
                    'post_id': post.id
                    }
                )
        ):
            response = self.client_auth.get(url)
            self.assertContains(response, '<img')

    def test_auth_client_add_comment(self):
        post = Post.objects.create(
            text='text first',
            author=self.user,
            group=self.group
        )
        comment_auth = self.client_auth.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.user,
                    'post_id': post.id
                    }
            ),
            data={
                'text': 'text first'
                  }
        )
        comment = self.client.get(
            reverse(
               'add_comment',
                kwargs={
                    'username': self.user,
                    'post_id': post.id
                }
            ),
            data={
                'text': 'text second'
            }
        )
        comments_auth = Comment.objects.filter(
            author__username=self.user.username, 
            text__contains = 'text first'
        )
        comments = Comment.objects.filter(
            author__username=self.user.username, 
            text__contains = 'text second'
        )
        self.assertTrue(comments_auth.exists())
        self.assertFalse(comments.exists())