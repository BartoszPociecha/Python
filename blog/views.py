from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from taggit.models import Tag

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug = tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3) #Trzy posty na każdej stronie
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        #jeżeli zmienna oage nie jest liczbą całkowitą
        #wówczas pobierana jest pierwsza strona wyniku
        posts = paginator.page(1)
    except EmptyPage:
        # Jeżeli zmienna ma wartość większą niż numer ostatniej strony
        # wyników w tedy pobierana jest ostatnia strona wyników
        posts = paginator.page(paginator.num_pages)
   # posts = Post.published.all()
    return render(request,
                  'blog/post/list.html',
                  {'page': page,
                    'posts': posts,
                   'tag': tag})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    comments = post.comments.filter(active=True)

    if request.method == "POST":
        # Komentarz został opublikowany
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Utworzenie obiektu Comment ale jeszcze nie zapisanie go w bazie danych
            new_comment = comment_form.save(commit=False)
            # Przypisanie bieżącego komentarza do posta
            new_comment.post = post
            # Zapisanie komentarza w bazie danych
            new_comment.save()
    else:
        comment_form = CommentForm()
    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'comment_form': comment_form})

def post_share(request, post_id):
    # Pobranie posta na podstawie jego identyfikatora
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        # Formularz został wysłany
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Weryfikacja pól formularza zakończyła się powodzeniem
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = '{} ({}) zachęca do przeczytania "{}"'.format(cd['name'],
                                                                    cd['email'], post.title)
            message = 'Przeczytaj post "{}" na stronie {}\n\n Komentarz dodany' \
                      'przez {}: {}'.format(post.title,post_url, cd['name'], cd['comments'])
            send_mail(subject, message, 'Bary@myblog.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})
# Create your views here.
