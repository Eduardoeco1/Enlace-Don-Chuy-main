from django.shortcuts import redirect

class SucursalActualMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Si cambiamos la sucursal desde CUALQUIER selector
        if request.method == 'GET' and 'sucursal_id' in request.GET:
            suc_id = request.GET.get('sucursal_id')
            
            # Guardamos la decisión en la sesión global
            request.session['sucursal_id'] = suc_id if suc_id != 'todas' else None
            
            # Limpiamos la URL para que no se quede pegado el parámetro,
            # pero CONSERVAMOS otros filtros como ?q= o ?categoria=
            query_params = request.GET.copy()
            query_params.pop('sucursal_id', None)
            
            nueva_url = request.path
            if query_params:
                nueva_url += '?' + query_params.urlencode()
                
            return redirect(nueva_url)

        # 2. Leemos la sesión y la inyectamos para que todas las vistas y templates la vean
        s_id = request.session.get('sucursal_id')
        request.sucursal_actual = None
        
        if s_id:
            from Sucursales.models import Sucursal
            try:
                request.sucursal_actual = Sucursal.objects.get(id=int(s_id))
            except:
                request.session['sucursal_id'] = None
        
        return self.get_response(request)
    

    