init python in custom_particles:
    from renpy.store import Transform, Text, NoRollback, config
    from math import pi, sin, cos

    class CustomParticles(renpy.Displayable, NoRollback):
        # Константы для настройки частиц:
        ALPHA_RANGE = (.25, .75)
        ZOOM_RANGE = (.25, .75)
        LIFETIME_RANGE = (2.5, .5)
        FADE_RANGE = (.9, .7) # Дипапзон резкости появления/затухания частицы
        FADE_SKEW_RANGE = (-.2, .2) # Диапазон перекоса между появлением и затуханием частицы

        def __init__(self, part_img=None, parts_count=300, speed=(60.0, 120.0), outborders=10):
            self.oldst = .0

            super(CustomParticles, self).__init__()

            self.part_img = renpy.displayable(part_img) 
            
            self.disp_size = (config.screen_width, config.screen_height)
            self.outborders = outborders

            self.speed = speed if not isinstance(speed, (int, float)) else (speed, speed)

            self.particles = [self.set_particle() for i in xrange(parts_count)]

        def set_particle(self, part_obj=None):
            # Координата в пределах экрана, с границами
            b, s = self.outborders, self.disp_size

            params = {
                "pos": tuple(renpy.random.randint(-b, c+b) for c in s),
                "angle": renpy.random.uniform(0, pi * 2.0),
                "speed": renpy.random.uniform(*self.speed),
                "lifetime": renpy.random.uniform(*self.LIFETIME_RANGE),
                "alpha": renpy.random.uniform(*self.ALPHA_RANGE),
                "zoom": renpy.random.uniform(*self.ZOOM_RANGE),
                "fade": renpy.random.uniform(*self.FADE_RANGE),
                "skew": renpy.random.uniform(*self.FADE_SKEW_RANGE)
                }

            if part_obj is None:
                return SingleParticle(self, self.part_img, **params)
            else:
                part_obj.reload_particle(**params)
                part_obj.need_reload = False


        def visit(self):
            return (part.disp for part in self.particles)

        def render(self, w, h, st, at):
            dt = st - self.oldst
            self.oldst = st

            rv = renpy.Render(*self.disp_size)
            
            for part in self.particles:
                rv.blit(part.disp.render(w, h, st, at), part.pos)
                if part.need_reload: self.set_particle(part)
                   
            renpy.redraw(self, .0)
            return rv

    class SingleParticle(renpy.object.Object):
        def __init__(self, host, disp, pos, angle, speed, lifetime, zoom, alpha, fade=.9, skew=.0):            
            self.pos = (.0, .0)         # Позиция частицы на экране
            self.direction = (.0, .0)   # Направление движения по x и y. Зависит от angle и speed

            self.lifetime = .0          # Время жизни частицы
            self.elapsed_time = .0      # Сколько она успела прожить?
            self.oldst = None

            # Размер и прозрачность, для трансформа:
            self.zoom = .0
            self.alpha = .0

            # Множители для интерполяции трапеции с перекосом
            self.__forward_slope = .0
            self.__backward_slope = .0

            # Здесь мы загружаем позиционные, временнЫе и прочие данные в частицу:
            self.reload_particle(pos, angle, speed, lifetime, zoom, alpha, fade, skew)
            self.need_reload = False

            # Границы, в которых будет двигаться частица:
            self.__borders, self.__borders_offset = host.disp_size, host.outborders

            self.disp = Transform(disp, alpha=.0, zoom=self.zoom, function=self.__trans_update)

        def reload_particle(self, pos, angle, speed, lifetime, zoom, alpha, fade, skew):
            self.pos = pos
            self.direction = speed * sin(angle), speed * -cos(angle)

            self.lifetime = lifetime
            self.elapsed_time = .0
            self.oldst = None

            self.zoom = zoom
            self.alpha = alpha

            self.__forward_slope = 1.0 / (max(1.0 - fade, 1e-5) * (1.0 - skew)) if skew > -1.0 else float("inf.")
            self.__backward_slope = 1.0 / (max(1.0 - fade, 1e-5) * (1.0 + skew)) if skew < 1.0 else float("inf.")

        def __trans_update(self, trans, st, at):
            if self.need_reload: return .0

            if self.oldst is None: self.oldst = st
            dt = st - self.oldst
            self.oldst = st
            self.elapsed_time += dt

            progress = self.elapsed_time / self.lifetime
            if progress >= 1.0:
                self.need_reload = True
                return .0

            trans.alpha = self.alpha * self.__trap_interpolate(progress)
            #trans.zoom = self.zoom * self.__trap_interpolate(progress)

            self.pos = (c + d * dt for c, d in zip(self.pos, self.direction))
            self.pos = tuple(wrap_around(c, s, self.__borders_offset) for c, s in zip(self.pos, self.__borders))

            return .0

        def __trap_interpolate(self, x):
            return clamp(min(x * self.__forward_slope, (1.0 - x) * self.__backward_slope) * 2.0)

    def wrap_around(val, val_range, offset=0):
        """
        Зацикливает координаты частицы, вышедшей за границы экрана
        """
        return (val + offset) % (val_range + offset * 2.0) - offset

    def clamp(val, min_val=.0, max_val=1.0):
        return max(min_val, min(val, max_val))

    def procedural_particle(size=16, color="#fe8", blur=2):
        """
        Возвращает программно-сгенерированную частицу
        """
        return Transform(Text("•", size=int(size)*2, color=color), blur=blur)

init python:
    # Выводим частички из кастомного namespac'а
    CustomParticles = custom_particles.CustomParticles
    