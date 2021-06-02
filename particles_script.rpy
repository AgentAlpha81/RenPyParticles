init python:    
    from renpy.display.transform import polar_to_cartesian
    
    class Vector(renpy.object.Object):
        """
        Честно скомунизженно.
        """
        def __init__(self, *data):
            self.data = data
            
        def __repr__(self):
            return repr(self.data) 
            
        def __add__(self, other):
            return tuple((a+b for a,b in zip(self.data, other.data)))
            
        def __sub__(self, other):
            return tuple((a-b for a,b in zip(self.data, other.data)))
            
    class SingleParticle(renpy.object.Object):
        """
        Класс одной частицы
        """
        def __init__(self, sp, fp, t, rt, ft, zoom, alpha, st):
            self.start_pos = sp 
            self.finish_pos = fp
            
            self.part_time = t
            self.rise_time = rt 
            self.fall_time = ft 
            
            self.max_zoom = zoom 
            self.max_alpha = alpha
            
            self.oldst = st
            self.pos = self.start_pos 
            self.zoom = .0
            self.alpha = .0
            
    class CustomParticles(renpy.Displayable):   
        from random import randint, uniform
        from math import sqrt, pow
        
        def __init__(self, part_img, parts_count=300):
            super(CustomParticles, self).__init__()
            self.part_img = renpy.displayable(part_img)
            
            self.w, self.h = (config.screen_width, config.screen_height)
            
            #self.max_parts = parts_count
            self.particles = [self.make_particle() for i in xrange(parts_count)]
            
        def get_rand_cord(self, w, h):
            """
            Возвращает рандомную координату в пределах w, h
            """
            return self.randint(-100, w+100), self.randint(-100, h+100)
            
        def progress_calc(self, oldst, t, st):
            target = oldst + t 
            anim_time = target - st 
            res = 1.0 - anim_time / t
            
            if res < .0:
                return .0
            elif .0 <= res <= 1.0:
                return res 
            else:
                return 1.0
            
        def make_particle(self, st=float()):
            """
            Создаёт частицу. Возвращает объект SingleParticle
            """
            w, h, = self.w, self.h 
            
            start_pos = self.get_rand_cord(w, h)
            finish_pos = self.get_rand_cord(w, h)
            xdist, ydist = Vector(*finish_pos) - Vector(*start_pos)
            
            speed = self.uniform(90, 110)
            
            part_time = self.sqrt(self.pow(xdist, 2) + self.pow(ydist, 2)) / speed
            rise_time = part_time * self.uniform(.1, .25)
            fall_time = part_time * self.uniform(.1, .25)
            
            
            max_alpha = self.uniform(.25, .75)
            max_zoom = self.uniform(.25, .75)
            
            part = SingleParticle(start_pos,
                                  finish_pos,
                                  part_time,
                                  rise_time,
                                  fall_time,
                                  max_alpha,
                                  max_zoom,
                                  st)
            return part
            
        def update_particle(self, part_idx, st):
            part = self.particles[part_idx]
            
            t = part.part_time 
            rt = part.rise_time
            ft = part.fall_time 
            
            start_time = part.oldst
            rise_time = start_time + rt
            fall_time = start_time + t - ft
            
            anim_progress = self.progress_calc(start_time, t, st)
            rise_progress = self.progress_calc(rise_time, rt, st)
            fall_progress = self.progress_calc(fall_time, ft, st)
            
            rise_vs_fall = rise_progress - fall_progress
            
            part.pos = renpy.atl.interpolate(anim_progress,
                                             part.start_pos,
                                             part.finish_pos,
                                             (int, int))
            
            part.alpha = part.max_alpha * rise_vs_fall
            part.zoom = part.max_zoom * rise_vs_fall
            
            if anim_progress >= 1.0:
                self.particles.pop(part_idx)
                self.particles.append(self.make_particle(st))
            
            
        
        def visit(self):
            return [self.part_img for i in self.particles]
            
        def render(self, w, h, st, at):
            rv = renpy.Render(w, h)
            
            for idx, part in enumerate(self.particles):
                self.update_particle(idx, st)
                xpos, ypos = part.pos
                
                if 0 < xpos < w and 0 < ypos < h:
                    t = Transform(child=self.part_img, 
                                  alpha=part.alpha,
                                  zoom=part.zoom)
                
                    #Используем blit для оптимизации
                    tr = t.render(w, h, st, at)
                    rv.blit(tr, (xpos, ypos))
                
            renpy.redraw(self, .0)
            return rv
