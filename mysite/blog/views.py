# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm
from django.views.generic import ListView
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
# Create your views here.


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # 3 posts in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        #  if page not integer, deliver the 1st page
        posts = paginator.page(1)
    except EmptyPage:  # if page out of range, deliver last page
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/posts/list.html', {'page': page,
                                                    'posts': posts,
                                                    'tag': tag})


def post_detail(request, day, month, year, post):
    post = get_object_or_404(Post, slug=post,
                             publish__day=day, publish__month=month,
                             publish__year=year)
    return render(request, 'blog/posts/detail.html', {'post': post})

    # List of active comments for this post
    comments = post.comments.filter(active=True)
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags',
                                                                             '-publish')[:4]

    return render(request, 'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'comment_form': comment_form})


def post_share(request, post_id):   # retrive post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':   # if form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'],
                                                                   cd['email'],
                                                                   post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title,
                                                                     post_url,
                                                                     cd['name'],
                                                                     cd['comments'])
            send_mail(subject, message, 'admin@admin.com', [cd['to']])
            sent = True
    else:
            form = EmailPostForm()
    return render(request, 'blog/posts/share.html', {'post': post,
                                                     'form': form,
                                                     'sent': sent})
