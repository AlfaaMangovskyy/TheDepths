import pygame
from static import *

pygame.init()
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT), pygame.NOFRAME,
)
clock = pygame.time.Clock()

IMAGES = {
    _path.removesuffix(".png").replace("/", ".") : pygame.image.load(f"src/make/{_path}").convert_alpha() for _path in os.listdir("src/make")
}

arena = Arena()
arena.newEntity("spider", 5, 5, {})
arena.newEntity("spider", -5, 5, {})
arena.newEntity("spider", 5, -5, {})
arena.newEntity("spider", -5, -5, {})
arena.newEntity("big_spider", -9, -5, {})
arena.player.item = Item("shotgun")

running = True
while running:

    arena.tick()
    keymap = pygame.key.get_pressed()
    mouseX, mouseY = pygame.mouse.get_pos()
    camX, camY = arena.camera.get()

    for e in pygame.event.get():

        if e.type == pygame.KEYDOWN:

            if e.key == pygame.K_ESCAPE:
                pygame.quit()
                running = False
                break

        if e.type == pygame.MOUSEBUTTONDOWN:
            realX = (mouseX - WIDTH // 2) / arena.scale + camX
            realY = (mouseY - HEIGHT // 2) / arena.scale + camY

            if arena.player.item and arena.player.cooldown == 0:
                arena.player.item.attack(arena.player, (realX, realY))

    if not running: break

    # print(clock.get_fps()) #

    if keymap[pygame.K_w]:
        if keymap[pygame.K_a]:
            arena.player.x += -(1 / math.sqrt(2)) * arena.player.speed
            arena.player.y += -(1 / math.sqrt(2)) * arena.player.speed
        elif keymap[pygame.K_d]:
            arena.player.x += (1 / math.sqrt(2)) * arena.player.speed
            arena.player.y += -(1 / math.sqrt(2)) * arena.player.speed
        else:
            arena.player.y += -arena.player.speed

    elif keymap[pygame.K_s]:
        if keymap[pygame.K_a]:
            arena.player.x += -(1 / math.sqrt(2)) * arena.player.speed
            arena.player.y += (1 / math.sqrt(2)) * arena.player.speed
        elif keymap[pygame.K_d]:
            arena.player.x += (1 / math.sqrt(2)) * arena.player.speed
            arena.player.y += (1 / math.sqrt(2)) * arena.player.speed
        else:
            arena.player.y += arena.player.speed

    elif keymap[pygame.K_a]:
        if keymap[pygame.K_s]:
            arena.player.y += -(1 / math.sqrt(2)) * arena.player.speed
            arena.player.x += -(1 / math.sqrt(2)) * arena.player.speed
        elif keymap[pygame.K_w]:
            arena.player.y += (1 / math.sqrt(2)) * arena.player.speed
            arena.player.x += -(1 / math.sqrt(2)) * arena.player.speed
        else:
            arena.player.x += -arena.player.speed

    elif keymap[pygame.K_d]:
        if keymap[pygame.K_s]:
            arena.player.y += -(1 / math.sqrt(2)) * arena.player.speed
            arena.player.x += (1 / math.sqrt(2)) * arena.player.speed
        elif keymap[pygame.K_w]:
            arena.player.y += (1 / math.sqrt(2)) * arena.player.speed
            arena.player.x += (1 / math.sqrt(2)) * arena.player.speed
        else:
            arena.player.x += arena.player.speed

    # arena.newParticle("heart", arena.player.x, arena.player.y, 0, -0.025, FRAMERATE) #

    screen.fill("#030303")

    pygame.draw.rect(
        screen, "#FFFFFF",
        (
            (-arena.player.w / 2) * arena.scale + WIDTH // 2,
            (-arena.player.h / 2) * arena.scale + HEIGHT // 2,
            arena.player.w * arena.scale,
            arena.player.h * arena.scale,
        ),
    )

    for block in arena.player.getRoom().blocks:

        pygame.draw.rect(
            screen, "#FFFFFF",
            (
                (block.x - camX) * arena.scale + WIDTH // 2,
                (block.y - camY) * arena.scale + HEIGHT // 2,
                block.w * arena.scale,
                block.h * arena.scale,
            ),
        )

    for entity in arena.entities:

        image = IMAGES.get(f"entity_{entity.id}")
        screen.blit(
            image,
            (
                (entity.x - camX) * arena.scale + WIDTH // 2 - image.get_width() // 2,
                (entity.y - camY) * arena.scale + HEIGHT // 2 - image.get_height() // 2,
            )
        )

    for particle in arena.particles:

        image = IMAGES.get(f"particle_{particle.id}")
        screen.blit(
            image,
            (
                (particle.x - camX) * arena.scale + WIDTH // 2 - image.get_width() // 2,
                (particle.y - camY) * arena.scale + HEIGHT // 2 - image.get_height() // 2,
            )
        )

    # if arena.player.cooldown > 0:

    #     if arena.player.item.id == "sword":
    #         if arena.player.cooldown >= 35:
    #             step = arena.player.cooldown - 35



    heartw = (arena.player.hp - 1) * 20 + arena.player.hp * IMAGES.get("heart_icon").get_width()
    for n in range(arena.player.hp):
        screen.blit(IMAGES.get("heart_icon"), (
            WIDTH // 2 - heartw // 2 + (n - 1) * 20 + n * IMAGES.get("heart_icon").get_width(),
            HEIGHT - IMAGES.get("heart_icon").get_height() - 20,
        ))

    pygame.display.update()
    clock.tick(FRAMERATE)