from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry.update(admin.site._registry)

    def each_context(self, request):
        # FIXME: This is a hack around https://code.djangoproject.com/ticket/25519
        # It shouldn't be necessary anymore after Django 1.10 releases.
        context = super().each_context(request)
        script_name = request.META['SCRIPT_NAME']
        if context['site_url'] == '/' and script_name:
            context['site_url'] = script_name
        return context

site = MyAdminSite()
