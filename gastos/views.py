def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f'¡Bienvenid@ {usuario.username}! Cuenta creada.')
            return redirect('inicio')
    else:
        form = UserCreationForm()
    return render(request, 'gastos/registro.html', {'form': form})
