from django.contrib.sessions.middleware import SessionMiddleware

class CustomSessionMiddleware(SessionMiddleware):
    def process_response(self, request, response):
        # استدعاء الوظيفة الأصلية
        response = super().process_response(request, response)
        
        # إذا كانت الجلسة تنتهي عند إغلاق المتصفح
        if request.session.get_expire_at_browser_close():
            # تعيين خاصية SameSite و Secure للكوكيز
            if hasattr(response, 'cookies'):
                if 'sessionid' in response.cookies:
                    response.cookies['sessionid']['samesite'] = 'Lax'
                    response.cookies['sessionid']['secure'] = True
                    
                if 'csrftoken' in response.cookies:
                    response.cookies['csrftoken']['samesite'] = 'Lax'
                    response.cookies['csrftoken']['secure'] = True
        
        return response