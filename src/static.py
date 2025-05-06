import math
import random
import json
import os
# import sys

# ARGS = {}
# for i in range()

WIDTH = 1920
HEIGHT = 1080
FRAMERATE = 60

with open("src/data/items.json", "r") as source:
    ITEMDATA : dict = json.load(source)
    source.close()

with open("src/data/entities.json", "r") as source:
    ENTITYDATA : dict = json.load(source)
    source.close()

class Block:

    def __init__(self, x : int, y : int, w : int, h : int):
        self.x, self.y = x, y
        self.w, self.h = w, h

    def collides(self, player) -> tuple[bool, bool, bool, bool]:
        w, a, s, d = False, False, False, False
        if not isinstance(player, (Player, Entity)): return w, a, s, d

        if (player.x - player.w / 2 <= self.x + self.w and player.x + player.w / 2 >= self.x) and player.y - player.h / 2 <= self.y <= player.y + player.h / 2:
            player.y = self.y - player.h / 2
            w = True
        elif (player.x - player.w / 2 <= self.x + self.w and player.x + player.w / 2 >= self.x) and player.y - player.h / 2 <= self.y + self.h <= player.y + player.h / 2:
            player.y = self.y + self.h + player.h / 2
            s = True
        elif (player.y - player.h / 2 <= self.y + self.h and player.y + player.h / 2 >= self.y) and player.x - player.w / 2 <= self.x <= player.x + player.w / 2:
            player.x = self.x - player.w / 2
            a = True
        elif (player.y - player.h / 2 <= self.y + self.h and player.y + player.h / 2 >= self.y) and player.x - player.w / 2 <= self.x + self.w <= player.x + player.w / 2:
            player.x = self.x + self.w + player.w / 2
            d = True

        return w, a, s, d

    def __repr__(self) -> str:
        return f"Block({self.x}, {self.y}, {self.w}, {self.h})"



class Player:

    def __init__(self, arena, savedata : dict = {}):
        self.arena : Arena = arena
        self.save = savedata
        self.x : float = self.save.get("x", 0.0)
        self.y : float = self.save.get("y", 0.0)
        self.rx : int = self.save.get("rx", 0)
        self.ry : int = self.save.get("ry", 0)

        self.kb : int = 0
        self.kbangle : int = 0

        self.w : float = 0.75
        self.h : float = 0.75

        self.speed : float = 0.30
        self.item : Item | None = None

        self.cooldown : int = 0

        self.hp : int = 12

    def getRoom(self):
        return self.arena.getRoom(self.rx, self.ry)

    def damage(self, amount : int):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0

        for i in range(amount):
            angle = (2 * math.pi * i / amount) - math.pi / 2
            self.arena.newParticle(
                "heart", self.x, self.y,
                0.10 * math.cos(angle),
                0.10 * math.sin(angle),
                FRAMERATE // 4,
            )

    def knockback(self, force : int, angle : int):
        self.kb += force
        self.kbangle = angle

    def tick(self):

        if not self.getRoom():
            room = self.arena.generateRoom(self.rx, self.ry)
            self.arena.rooms.append(room)

        if self.cooldown > 0:
            self.cooldown -= 1

        if self.kb > 0:
            self.x += 0.15 * self.kb * math.cos(self.kbangle / 180 * math.pi)
            self.y += 0.15 * self.kb * math.sin(self.kbangle / 180 * math.pi)
            self.kb -= 1

        for block in self.getRoom().blocks:
            w, a, s, d = block.collides(self)


class Room:

    def __init__(self, rx : int, ry : int, w : int, h : int, blocks : list[Block] = []):
        self.rx, self.ry = rx, ry
        self.w, self.h = w, h
        self.blocks : list[Block] = blocks

        self.entities : list[Entity] = []
        self.ew, self.ea, self.es, self.ed = False, False, False, False

    def __repr__(self) -> str:
        return f"Room({self.rx}, {self.ry}, {self.blocks})"


class Camera:

    def __init__(self, player : Player):
        self.player = player
        self.x : float = player.x
        self.y : float = player.y

        self.shakeTimer : int = 0
        self.shakeForce : float = 0.0

    def tick(self):
        self.x = self.player.x
        self.y = self.player.y

        if self.shakeTimer > 0:
            self.shakeTimer -= 1
            if self.shakeTimer == 0:
                self.shakeForce = 0.0

    def shake(self, force : float, time : int):
        if force > self.shakeForce:
            self.shakeForce = force
        if time > self.shakeTimer:
            self.shakeTimer += time

    def get(self) -> tuple[float, float]:
        return (
            self.x + random.randint(-10, 10) / 100 * self.shakeForce,
            self.y + random.randint(-10, 10) / 100 * self.shakeForce,
        )

class Particle:

    def __init__(self, _id : str, x : float, y : float, vx : float, vy : float, t : int):
        self.id = _id
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.t = t
        self.timer = 0
        self.destroy : bool = False

    def tick(self):
        self.x += self.vx
        self.y += self.vy
        self.timer += 1
        if self.timer >= self.t:
            self.destroy = True

class Entity:

    def __init__(self, arena, _id : str, x : float, y : float, meta : dict = {}):
        self.arena : Arena = arena
        self.id = _id
        self.x = x
        self.y = y
        self.meta = meta
        self.timer : int = 0

        self._data : dict = ENTITYDATA.get(self.id, {})

        self.maxHP : int = self._data.get("hp", 3)
        self.hp : int = self.maxHP
        self.hurtable : bool = self._data.get("hurtable", True)
        self.killCountdown : int = 0

        self.kb : int = 0
        self.kbangle : int = 0

        self.w : float = self._data.get("hx", 0.75)
        self.h : float = self._data.get("hy", 0.75)

        self.destroy : bool = False

    def knockback(self, force : int, angle : int):
        self.kb += force
        self.kbangle = angle

    def tick(self):

        if self.kb > 0:
            self.x += 0.15 * self.kb * math.cos(self.kbangle / 180 * math.pi)
            self.y += 0.15 * self.kb * math.sin(self.kbangle / 180 * math.pi)
            self.kb -= 1

        if self.killCountdown > 0:
            self.killCountdown -= 1
            if self.killCountdown == 0:
                self.destroy = True
                return

        for block in self.arena.player.getRoom().blocks:
            w, a, s, d = block.collides(self)

        if self.x < -self.arena.player.getRoom().w // 2 + self.w / 2:
            self.x = -self.arena.player.getRoom().w // 2 + self.w / 2
        if self.x > self.arena.player.getRoom().w // 2 - self.w / 2:
            self.x = self.arena.player.getRoom().w // 2 - self.w / 2
        if self.y < -self.arena.player.getRoom().h // 2 + self.h / 2:
            self.y = -self.arena.player.getRoom().h // 2 + self.h / 2
        if self.y > self.arena.player.getRoom().h // 2 - self.h / 2:
            self.y = self.arena.player.getRoom().h // 2 - self.h / 2

        self.timer += 1
        if self.killCountdown == 0:
            return getattr(self, f"tick_{self.id}", self.tick_null)()

    def damage(self, amount : int):
        if not self.hurtable: return

        for i in range(amount):
            angle = (2 * math.pi * i / amount) - math.pi / 2
            self.arena.newParticle(
                "heart", self.x, self.y,
                0.10 * math.cos(angle),
                0.10 * math.sin(angle),
                FRAMERATE // 4,
            )

        return getattr(self, f"damage_{self.id}", self.damage_null)(amount)

    def animate(self):
        return getattr(self, f"animate_{self.id}", self.animate_null)()

    def tick_null(self):
        return
    def damage_null(self, amount : int):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.killCountdown = FRAMERATE // 3
            self.arena.camera.shake(1.5, FRAMERATE // 10)
        return amount
    def animate_null(self):
        return f"entity_{self.id}"

    def tick_spider(self):
        if not "cooldown" in self.meta.keys():
            self.meta["cooldown"] = 0

        angle = math.atan2(
            self.y - self.arena.player.y,
            self.x - self.arena.player.x,
        )
        distance = math.sqrt(
            (self.y - self.arena.player.y) ** 2 + (self.x - self.arena.player.x) ** 2,
        )

        if distance <= 0.75:
            if self.meta["cooldown"] == 0:
                self.arena.player.damage(1)
                self.meta["cooldown"] = FRAMERATE
        else:
            self.x += -0.10 * math.cos(angle)
            self.y += -0.10 * math.sin(angle)

        if self.meta["cooldown"] > 0:
            self.meta["cooldown"] -= 1

    def tick_big_spider(self):
        if not "cooldown" in self.meta.keys():
            self.meta["cooldown"] = 0

        angle = math.atan2(
            self.y - self.arena.player.y,
            self.x - self.arena.player.x,
        )
        distance = math.sqrt(
            (self.y - self.arena.player.y) ** 2 + (self.x - self.arena.player.x) ** 2,
        )

        if distance <= 0.75:
            if self.meta["cooldown"] == 0:
                self.arena.player.damage(3)
                self.meta["cooldown"] = FRAMERATE * 2
        else:
            self.x += -0.075 * math.cos(angle)
            self.y += -0.075 * math.sin(angle)

        if self.meta["cooldown"] > 0:
            self.meta["cooldown"] -= 1

    # def damage_spider(self, amount : int):
    #     self.hp -= amount
    #     if self.hp <= 0:
    #         self.hp = 0
    #         self.destroy = True
    #     return amount

    def tick_bullet(self):
        if not "direction" in self.meta.keys():
            self.destroy = True
            return

        if self.timer >= FRAMERATE // 2:
            self.destroy = True
            return

        self.x += 0.75 * math.cos(self.meta["direction"] / 180 * math.pi)
        self.y += 0.75 * math.sin(self.meta["direction"] / 180 * math.pi)

        for block in self.arena.player.getRoom().blocks:
            if block.x <= self.x <= block.x + block.w:
                if block.y <= self.y <= block.y + block.h:
                    self.destroy = True
                    return

        for entity in self.arena.player.getRoom().entities:
            if not entity.hurtable: continue
            distance = math.sqrt(
                (self.x - entity.x) ** 2 + (self.y - entity.y) ** 2,
            )
            if distance <= (entity.w + entity.h) / 2:
                entity.damage(2)
                entity.knockback(1, self.meta["direction"])
                self.arena.camera.shake(1.0, FRAMERATE // 10)
                self.destroy = True
                return

class Item:

    def __init__(self, _id : str):
        self.id = _id
        self._data = ITEMDATA.get(self.id, {})
        self.name = self._data.get("name", "???")
        self.desc = self._data.get("desc", "???")
        self.cooldown : int = self._data.get("cooldown", FRAMERATE)

    def attack(self, player : Player, pos : tuple[float, float]):
        getattr(self, f"attack_{self.id}", self.attack_null)(player, pos)

    def attack_null(self, player : Player, pos : tuple[float, float]):
        return

    def attack_sword(self, player : Player, pos : tuple[float, float]):

        angle = math.atan2(
            player.y - pos[1],
            player.x - pos[0],
        ) * 180 / math.pi
        distance = math.sqrt(
            (player.y - pos[1]) ** 2 + (player.x - pos[0]) ** 2,
        )

        hit = False
        for target in player.arena.player.getRoom().entities:
            distance = math.sqrt(
                (player.y - pos[1]) ** 2 + (player.x - pos[0]) ** 2,
            )
            targetAngle = math.atan2(
                player.y - pos[1],
                player.x - pos[0],
            ) * 180 / math.pi

            if distance <= 3 and angle - 10 <= targetAngle <= angle + 10:
                target.damage(2)
                hit = True

        for i in range(-10, 10 + 1, 5):
            player.arena.newParticle(
                "steel",
                player.x - 3 * math.cos((angle + i) / 180 * math.pi),
                player.y - 3 * math.sin((angle + i) / 180 * math.pi),
                0.10 * math.cos((angle + i) / 180 * math.pi),
                0.10 * math.sin((angle + i) / 180 * math.pi),
                FRAMERATE // 2
            )
        for i in range(-10, 10 + 1, 5):
            player.arena.newParticle(
                "steel",
                player.x - 3 * math.cos((angle + i) / 180 * math.pi),
                player.y - 3 * math.sin((angle + i) / 180 * math.pi),
                0.15 * math.cos((angle + i) / 180 * math.pi),
                0.15 * math.sin((angle + i) / 180 * math.pi),
                FRAMERATE // 2
            )
        for i in range(-10, 10 + 1, 5):
            player.arena.newParticle(
                "steel",
                player.x - 3 * math.cos((angle + i) / 180 * math.pi),
                player.y - 3 * math.sin((angle + i) / 180 * math.pi),
                0.20 * math.cos((angle + i) / 180 * math.pi),
                0.20 * math.sin((angle + i) / 180 * math.pi),
                18,
            )

        player.cooldown += self.cooldown

    def attack_shotgun(self, player : Player, pos : tuple[float, float]):

        angle = math.atan2(
            player.y - pos[1],
            player.x - pos[0],
        ) * 180 / math.pi##

        player.knockback(2, angle)

        player.arena.camera.shake(0.8, FRAMERATE // 10)
        for t in range(-12, 12 + 1, 4):
            theta = (angle + t)
            player.arena.newEntity(
                "bullet",
                player.x - 0.25 * math.cos(theta / 180 * math.pi),
                player.y - 0.25 * math.sin(theta / 180 * math.pi),
                {"direction" : theta + 180}
            )

        player.cooldown += self.cooldown

class Arena:

    def __init__(self, savedata : dict = {}):
        self.player = Player(self, savedata.get("player", {}))
        self.camera = Camera(self.player)
        self.rooms : list[Room] = []

        self.particles : list[Particle] = []
        # self.entities : list[Entity] = []

        self.scale : int = 75

    def getRoom(self, rx : int, ry : int) -> Room | None:
        found = None
        for room in self.rooms:
            if (room.rx, room.ry) == (rx, ry):
                found = room
                break

        return found

    def generateRoom(self, rx : int, ry : int, dx : int = 0, dy : int = 0) -> Room:
        DIFFICULTY = 1 + math.floor(math.sqrt(rx ** 2 + ry ** 2))
        room = Room(rx, ry, 20, 20, [])
        # room.blocks.append(Block(-1, -1, 2, 2))
        room.blocks.append(Block(-10, -10, 3, 3))
        room.blocks.append(Block(-10, 7, 3, 3))
        room.blocks.append(Block(7, -10, 3, 3))
        room.blocks.append(Block(7, 7, 3, 3))

        # dx = rx - self.player.rx
        # dy = ry - self.player.ry

        w, a, s, d = False, False, False, False

        print(rx, ry, dx, dy)
        if dx < 0:
            room.blocks.append(Block(8, -7, 2, 5))
            room.blocks.append(Block(8, 2, 2, 5))
            room.ed = True
            d = True
        if dx > 0:
            room.blocks.append(Block(-10, -7, 2, 5))
            room.blocks.append(Block(-10, 2, 2, 5))
            room.ea = True
            a = True
        if dy < 0:
            room.blocks.append(Block(-7, 8, 5, 2))
            room.blocks.append(Block(2, 8, 5, 2))
            room.es = True
            s = True
        if dy > 0:
            room.blocks.append(Block(-7, -10, 5, 2))
            room.blocks.append(Block(2, -10, 5, 2))
            room.ew = True
            w = True

        if not a:
            if random.randint(1, 2) == 1:
                can = True
                if self.getRoom(rx - 1, ry):
                    if not self.getRoom(rx - 1, ry).ed:
                        can = False
                if can:
                    room.blocks.append(Block(-10, -7, 2, 5))
                    room.blocks.append(Block(-10, 2, 2, 5))
                    room.ea = True
                else:
                    room.blocks.append(Block(-10, -7, 2, 14))
            else:
                room.blocks.append(Block(-10, -7, 2, 14))
            a = True

        if not d:
            if random.randint(1, 2) == 1:
                can = True
                if self.getRoom(rx + 1, ry):
                    if not self.getRoom(rx + 1, ry).ea:
                        can = False
                if can:
                    room.blocks.append(Block(8, -7, 2, 5))
                    room.blocks.append(Block(8, 2, 2, 5))
                    room.ed = True
                else:
                    room.blocks.append(Block(8, -7, 2, 14))
            else:
                room.blocks.append(Block(8, -7, 2, 14))
            d = True

        if not s:
            if random.randint(1, 2) == 1:
                can = True
                if self.getRoom(rx, ry + 1):
                    if not self.getRoom(rx, ry + 1).ew:
                        can = False
                if can:
                    room.blocks.append(Block(-7, 8, 5, 2))
                    room.blocks.append(Block(2, 8, 5, 2))
                    room.es = True
                else:
                    room.blocks.append(Block(-7, 8, 14, 2))
            else:
                room.blocks.append(Block(-7, 8, 14, 2))
            s = True

        if not w:
            if random.randint(1, 2) == 1:
                can = True
                if self.getRoom(rx, ry - 1):
                    if not self.getRoom(rx, ry - 1).es:
                        can = False
                if can:
                    room.blocks.append(Block(-7, -10, 5, 2))
                    room.blocks.append(Block(2, -10, 5, 2))
                    room.ew = True
                else:
                    room.blocks.append(Block(-7, -10, 14, 2))
            else:
                room.blocks.append(Block(-7, -10, 14, 2))
            w = True



        """
        SPAWNING ENTITIES
        """
        if DIFFICULTY > 1:
            R = random.randint(1, sum(range(1, DIFFICULTY + 1, 1)))
            for i in range(DIFFICULTY, 0, -1):
                if i >= R:
                    break
                else:
                    R -= i
            i = DIFFICULTY - i

            # if random.randint(1, 2) == 1: #
            for n in range(i):
                room.entities.append(Entity(
                    self,
                    "spider" if random.randint(1, 5) != 1 else "big_spider",
                    5 * math.cos((360 * n / i) / 180 * math.pi),
                    5 * math.sin((360 * n / i) / 180 * math.pi),
                ))

        return room

    def newParticle(self, _id : str, x : float, y : float, vx : float, vy : float, t : int):
        particle = Particle(_id, x, y, vx, vy, t)
        self.particles.append(particle)
        return particle

    def newEntity(self, _id : str, x : float, y : float, meta : dict = {}):
        entity = Entity(self, _id, x, y, meta)
        self.player.getRoom().entities.append(entity)
        return entity

    def tick(self):

        self.player.tick()
        self.camera.tick()

        for particle in self.particles:
            particle.tick()
            if particle.destroy:
                self.particles.remove(particle)
                del particle

        for entity in self.player.getRoom().entities:
            entity.tick()
            if entity.destroy:
                self.player.getRoom().entities.remove(entity)
                del entity

        if self.player.x <= -self.player.getRoom().w / 2:
            w = self.player.getRoom().w
            self.player.rx -= 1
            self.player.x = (w // 2 - 0.5)
            self.player.y = 0

            if not self.player.getRoom():
                room = self.generateRoom(self.player.rx, self.player.ry, -1, 0)
                self.rooms.append(room)

        elif self.player.x >= self.player.getRoom().w / 2:
            w = self.player.getRoom().w
            self.player.rx += 1
            self.player.x = -(w // 2 - 0.5)
            self.player.y = 0

            if not self.player.getRoom():
                room = self.generateRoom(self.player.rx, self.player.ry, 1, 0)
                self.rooms.append(room)

        elif self.player.y <= -self.player.getRoom().h / 2:
            h = self.player.getRoom().h
            self.player.ry -= 1
            self.player.x = 0
            self.player.y = (h // 2 - 0.5)

            if not self.player.getRoom():
                room = self.generateRoom(self.player.rx, self.player.ry, 0, -1)
                self.rooms.append(room)

        elif self.player.y >= self.player.getRoom().h / 2:
            h = self.player.getRoom().h
            self.player.ry += 1
            self.player.x = 0
            self.player.y = -(h // 2 - 0.5)

            if not self.player.getRoom():
                room = self.generateRoom(self.player.rx, self.player.ry, 0, 1)
                self.rooms.append(room)

        # print(self.rooms)