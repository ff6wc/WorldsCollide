from data.sketch import Sketch
from data.structures import DataArray
from memory.space import Reserve, Bank, Write, Read
import instruction.asm as asm

class Sketches():
    ATTACKS_DATA_START = 0xf4300
    ATTACKS_DATA_END = 0xf45ff
    ATTACKS_DATA_SIZE = 2

    def __init__(self, rom, args, enemies, rages):
        self.rom = rom
        self.args = args
        self.enemies = enemies
        self.rages = rages

        self.attack_data = DataArray(self.rom, self.ATTACKS_DATA_START, self.ATTACKS_DATA_END, self.ATTACKS_DATA_SIZE)

        self.sketches = []
        for sketch_index in range(len(self.attack_data)):
            sketch = Sketch(sketch_index, self.attack_data[sketch_index])
            self.sketches.append(sketch)

    def enable_sketch_chances_always(self):
        # Always Sketch if the target is valid
        # NOPing the JSR and BCS that can prevent Sketch from working
        space = Reserve(0x023b3d, 0x023b41, "sketch always", asm.NOP())

    def enable_sketch_casters_stats(self):
        # Based on https://www.ff6hacking.com/forums/thread-3478.html

        # New subroutine. Note that most of this logic is the same as vanilla logic at C2/2954.
        src = [
            # A = Character using sketch (from $3417)
            asm.BMI("exit"),            #Branch if no Sketcher
            asm.TAX(),                  #if there's a valid Sketcher, use their Level for attack by making X = character offset
            asm.LDA(0x11A2, asm.ABS),   #Spell Properties
            asm.LSR(),                  #Check if Physical/Magical
            asm.LDA(0x3B41, asm.ABS_X), #Sketcher's Mag.Pwr
            asm.BCC("magical"),         #Branch if not physical damage
            asm.LDA(0x3B2C, asm.ABS_X), #Sketcher's Vigor * 2
            "magical",           
            asm.STA(0x11AE, asm.ABS),   #Set Sketcher's Magic or Vigor
            "exit",
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "Sketch Caster Stats")
        use_sketcher_stats_addr = space.start_address
        
        # Call our new subroutine
        space = Reserve(0x22c25, 0x22c27, "jump to new routine")
        space.write(
            asm.JSR(use_sketcher_stats_addr, asm.ABS)
        )

        # While the above subroutine loads Mag Pwr and Vigor, particularly for sketched spells, it doesn't handle Hit/Fight/Special BatPwr or weapon specials. 
        # Therefore, we're going to replace the X in all of the C2/299F subroutine with the sketcher/controller.
        src = [
            asm.STX(0x10, asm.DIR),   # store X into scratchpad -- we'll restore it below near the end of the C2/299F routine
            asm.LDA(0x3417, asm.ABS), # get Sketcher
            asm.BMI("check_control"), # branch if not sketcher
            asm.TAX(),                # if there's a valid sketcher, set them as X for all of the C2/299F routine
            "check_control",
            asm.LDA(0x32B9,asm.ABS_X),# who's Controlling this entity?
            asm.CMP(0xFF, asm.IMM8),
            asm.BEQ("exit"),          # branch if nobody controls them
            asm.TAX(),                # if there's a valid controller, user their stats
            "exit",
            Read(0x229a0, 0x229a2),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "Sketch/Control Casters Weapon stats")
        use_sketcher_controller_weapon_stats_addr = space.start_address

        space = Reserve(0x229a0, 0x229a2, "jump to sketch/control weapon stats")
        space.write(
            asm.JSR(use_sketcher_controller_weapon_stats_addr, asm.ABS)
        )

        # restore X for the remainder of C2/299F. The only impact of doing it this early is that if the enemy is imped, the sketch/controlled attack will be weak.
        src = [
            asm.LDX(0x10, asm.DIR), # restore X from scratchpad
            asm.STZ(0x10, asm.DIR), # zero out scratchpad just in case
            Read(0x22a1b, 0x22a1d), # displaced code
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "Sketch/Control Casters Weapon stats end")
        use_sketcher_controller_weapon_stats_end_addr = space.start_address

        space = Reserve(0x22a1b, 0x22a1d, "jump to sketch/control weapon stats end")
        space.write(
            asm.JSR(use_sketcher_controller_weapon_stats_end_addr, asm.ABS),
        )


    def enable_sketch_improved_abilities(self):
        from data.spell_names import name_id
        from data.sketch_custom_commands import custom_commands

        for sketch in self.sketches:
            # if either is Battle, replace with opposite
            if sketch.rare == name_id["Battle"]:
                sketch.rare = sketch.common
            if sketch.common == name_id["Battle"]:
                sketch.common = sketch.rare
            # If both are Battle, replace both with Rage (if it exists)
            if sketch.rare == name_id["Battle"] and sketch.common == name_id["Battle"]:
                if sketch.id < self.rages.RAGE_COUNT:
                    rage = self.rages.rages[sketch.id]
                    sketch.rare = rage.attack2
                    sketch.common = rage.attack2
            # If both are identical, replace rare with Rage (if it exists)
            if sketch.rare == sketch.common:
                if sketch.id < self.rages.RAGE_COUNT:
                    sketch.rare = self.rages.rages[sketch.id].attack2
            # Override with custom commands
            if sketch.id in custom_commands:
                sketch.rare = custom_commands[sketch.id][0]
                sketch.common = custom_commands[sketch.id][1]

    def mod(self):
        if self.args.sketch_control_improved_stats:
            self.enable_sketch_chances_always()
            self.enable_sketch_casters_stats()
        if self.args.sketch_control_improved_abilities:
            self.enable_sketch_improved_abilities()

    def write(self):
        if self.args.spoiler_log:
            self.log()

        for sketch_index, sketch in enumerate(self.sketches):
            self.attack_data[sketch_index] = sketch.attack_data()

        self.attack_data.write()

    def log(self):
        pass

    def print(self):
        for sketch in self.sketches:
            sketch.print()
