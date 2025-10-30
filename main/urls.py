from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),

    # ----- events -----
    path('events/', views.public_events_list_view, name='public_events_list'),
    path('events/<int:event_id>/', views.public_event_detail_view, name='public_event_detail'),
    path('events/<int:event_id>/weather/', views.public_event_weather_view, name='public_event_weather'),


   # ----- blog -----
    path('blog/', views.public_article_list_view, name='public_article_list'),
    path('blog/<int:article_id>/', views.public_article_detail_view, name='public_article_detail'),

   # ----- artworks -----
    path('artworks/', views.public_artwork_list_view, name='public_artwork_list'),
    path('artworks/<int:artwork_id>/', views.public_artwork_detail_view, name='public_artwork_detail'),

   # ----- workshops -----
    path('workshops', views.public_workshop_list_view, name='public_workshop_list'),
    path('workshops/<int:workshop_id>/', views.public_workshop_detail_view, name='public_workshop_detail'),
    path('workshops/<int:workshop_id>/weather/', views.public_workshop_weather_view, name='public_workshop_weather'),

   # ----- ai -----
    path("ai-image/", views.ai_image_generator_page, name="ai_image_generator"),
    path("ai-bg-remove/", views.ai_background_remover_page, name="ai_background_remover"),
    path("ai-photo-editor/", views.ai_photo_editor_page, name="ai_photo_editor"),


    #---------------------- ai emotion detector --------------------------
    path("emotion/", views.emotion_page, name="emotion_page"),
    path("emotion/analyze/", views.emotion_analyze, name="emotion_analyze"),
    path("emotion/recommend/", views.recommend_artworks_for_emotion, name="emotion_recommend"),



    #---------------------- chatbot --------------------------
    path("ai-chat/", views.ai_chat_page, name="ai_chat_page"),
    path("ai-chat/send/", views.ai_chat_send, name="ai_chat_send"),


    #---------------------- ml model --------------------------
    path("identify/", views.identify_artist_view, name="identify-artist"),
    path("predict-price/", views.price_predict_view, name="predict-price"),

]
