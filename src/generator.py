from block import Program, Block, IF, Increment, Decrement, Assign
import os

def generate_config(path, config_variables):
    with open("{}{}".format(path, "Config.h"), 'w') as f:
        for var_name, value in config_variables:
            f.write("const int {} = {};\n".format(var_name, value))

def generate_commands(path, setup_lines, commands):
    with open("{}{}".format(path, "Commands.h"), 'w') as f:
        f.write('''#include "../../Joystick.h"
#include <avr/pgmspace.h>
#define SPAM_DURATION 1
static const int setup_lines = {};
static const int close_lines = {};
static const Command m_command[] PROGMEM = {{
'''.format(setup_lines, len(commands) - 1))
        f.write(',\n'.join(['\t{{{}, {}}}'.format(a,b) for a,b in commands]))
        f.write('\n};')

def block_to_string(block):
    start, end = block.command_range
    return "\tcommandIndex = {};\n\t\t\t\t\t\tm_endIndex = {};\n\t\t\t\t\t\tcurr_process = {};\n".format(start, end, block.block_num)

def generate_c_file(name, path, variables, blocks):
    with open("{}{}.c".format(path, name), 'w') as f:
        f.write('''/*
Pokemon Sword & Shield Fast Egg Collector - Proof-of-Concept

Based on the LUFA library's Low-Level Joystick Demo
	(C) Dean Camera
Based on the HORI's Pokken Tournament Pro Pad design
	(C) HORI

This project implements a modified version of HORI's Pokken Tournament Pro Pad
USB descriptors to allow for the creation of custom controllers for the
Nintendo Switch. This also works to a limited degree on the PS3.

Since System Update v3.0.0, the Nintendo Switch recognizes the Pokken
Tournament Pro Pad as a Pro Controller. Physical design limitations prevent
the Pokken Controller from functioning at the same level as the Pro
Controller. However, by default most of the descriptors are there, with the
exception of Home and Capture. Descriptor modification allows us to unlock
these buttons for our use.
*/

#include "../../Joystick.h"
#include <stdbool.h>
#include "Commands.h"
#include "Config.h"

// Main entry point.
int main(void) {
	// We'll start by performing hardware and peripheral setup.
	SetupHardware();
	// We'll then enable global interrupts for our use.
	GlobalInterruptEnable();
	// Once that's done, we'll enter an infinite loop.
	for (;;)
	{
		// We need to run our task to process and deliver data for our IN and OUT endpoints.
		HID_Task();
		// We also need to run the main USB management task.
		USB_USBTask();
	}
}

// Configures hardware and peripherals, such as the USB peripherals.
void SetupHardware(void) {
	// We need to disable watchdog if enabled by bootloader/fuses.
	MCUSR &= ~(1 << WDRF);
	wdt_disable();

	// We need to disable clock division before initializing the USB hardware.
	//clock_prescale_set(clock_div_1);
	// We can then initialize our hardware and peripherals, including the USB stack.

	#ifdef ALERT_WHEN_DONE
	// Both PORTD and PORTB will be used for the optional LED flashing and buzzer.
	#warning LED and Buzzer functionality enabled. All pins on both PORTB and \
PORTD will toggle when printing is done.
	DDRD  = 0xFF; //Teensy uses PORTD
	PORTD =  0x0;
                  //We'll just flash all pins on both ports since the UNO R3
	DDRB  = 0xFF; //uses PORTB. Micro can use either or, but both give us 2 LEDs
	PORTB =  0x0; //The ATmega328P on the UNO will be resetting, so unplug it?
	#endif
	// The USB stack should be initialized last.
	USB_Init();
}

// Fired to indicate that the device is enumerating.
void EVENT_USB_Device_Connect(void) {
	// We can indicate that we're enumerating here (via status LEDs, sound, etc.).
}

// Fired to indicate that the device is no longer connected to a host.
void EVENT_USB_Device_Disconnect(void) {
	// We can indicate that our device is not ready (via status LEDs, sound, etc.).
}

// Fired when the host set the current configuration of the USB device after enumeration.
void EVENT_USB_Device_ConfigurationChanged(void) {
	bool ConfigSuccess = true;

	// We setup the HID report endpoints.
	ConfigSuccess &= Endpoint_ConfigureEndpoint(JOYSTICK_OUT_EPADDR, EP_TYPE_INTERRUPT, JOYSTICK_EPSIZE, 1);
	ConfigSuccess &= Endpoint_ConfigureEndpoint(JOYSTICK_IN_EPADDR, EP_TYPE_INTERRUPT, JOYSTICK_EPSIZE, 1);

	// We can read ConfigSuccess to indicate a success or failure at this point.
}

// Process control requests sent to the device from the USB host.
void EVENT_USB_Device_ControlRequest(void) {
	// We can handle two control requests: a GetReport and a SetReport.

	// Not used here, it looks like we don't receive control request from the Switch.
}

// Process and deliver data from IN and OUT endpoints.
void HID_Task(void) {
	// If the device isn't connected and properly configured, we can't do anything here.
	if (USB_DeviceState != DEVICE_STATE_Configured)
		return;

	// We'll start with the OUT endpoint.
	Endpoint_SelectEndpoint(JOYSTICK_OUT_EPADDR);
	// We'll check to see if we received something on the OUT endpoint.
	if (Endpoint_IsOUTReceived())
	{
		// If we did, and the packet has data, we'll react to it.
		if (Endpoint_IsReadWriteAllowed())
		{
			// We'll create a place to store our data received from the host.
			USB_JoystickReport_Output_t JoystickOutputData;
			// We'll then take in that data, setting it up in our storage.
			while(Endpoint_Read_Stream_LE(&JoystickOutputData, sizeof(JoystickOutputData), NULL) != ENDPOINT_RWSTREAM_NoError);
			// At this point, we can react to this data.

			// However, since we're not doing anything with this data, we abandon it.
		}
		// Regardless of whether we reacted to the data, we acknowledge an OUT packet on this endpoint.
		Endpoint_ClearOUT();
	}

	// We'll then move on to the IN endpoint.
	Endpoint_SelectEndpoint(JOYSTICK_IN_EPADDR);
	// We first check to see if the host is ready to accept data.
	if (Endpoint_IsINReady())
	{
		// We'll create an empty report.
		USB_JoystickReport_Input_t JoystickInputData;
		// We'll then populate this report with what we want to send to the host.
		GetNextReport(&JoystickInputData);
		// Once populated, we can output this data to the host. We do this by first writing the data to the control stream.
		while(Endpoint_Write_Stream_LE(&JoystickInputData, sizeof(JoystickInputData), NULL) != ENDPOINT_RWSTREAM_NoError);
		// We then send an IN packet on this endpoint.
		Endpoint_ClearIN();
	}
}

typedef enum {
	PROCESS,
	DONE
} State_t;
State_t state = PROCESS;

uint8_t curr_process = 0;

#define ECHOES 5
int echoes = 0;
USB_JoystickReport_Input_t last_report;

Command tempCommand;
int durationCount = 0;

// start and end index of "Setup"
int commandIndex = ''' + str(blocks[0].command_range[0]) + ''';
int m_endIndex = setup_lines;
''')
        for var_name, value in variables:
            f.write("int {} = {};\n".format(var_name, value))
        f.write('''// Prepare the next report for the host.
void GetNextReport(USB_JoystickReport_Input_t* const ReportData) {

	// Prepare an empty report
	memset(ReportData, 0, sizeof(USB_JoystickReport_Input_t));
	ReportData->LX = STICK_CENTER;
	ReportData->LY = STICK_CENTER;
	ReportData->RX = STICK_CENTER;
	ReportData->RY = STICK_CENTER;
	ReportData->HAT = HAT_CENTER;

	// Repeat ECHOES times the last report
	if (echoes > 0)
	{
		memcpy(ReportData, &last_report, sizeof(USB_JoystickReport_Input_t));
		echoes--;
		return;
	}

	// States and moves management
	switch (state)
	{
		case PROCESS:
			// Get the next command sequence (new start and end)
			if (commandIndex == -1)
			{
				if (false)
				{
					state = DONE;
					break;
				}
                \n''')
        for i,block in enumerate(blocks):
            f.write('\t\t\t\telse if(curr_process == {}) {{\n'.format(i))
            if not block.next_block:
                f.write('\t\t\t\t\tstate = DONE;\n')
                f.write('\t\t\t\t\tbreak;\n')
            elif isinstance(block.next_block, Block):
                f.write("\t\t\t\t\t" + block_to_string(block.next_block))
            elif isinstance(block.next_block, IF):
                f.write('\t\t\t\t\tif({}){{\n'.format(block.next_block.condition))
                f.write("\t\t\t\t\t" + block_to_string(block.next_block.true_block))
                f.write('\t\t\t\t\t}\n')
                if(block.next_block.false_block):
                    f.write('\t\t\t\t\telse {\n')
                    f.write("\t\t\t\t\t" + block_to_string(block.next_block.false_block))
                    f.write('\t\t\t\t\t}\n')
            if block.assignments:
                for assignment in block.assignments:
                    if(isinstance(assignment, Assign)):
                        f.write('\t\t\t\t\t\t{} = {};\n'.format(assignment.variable_name, assignment.value))
                    elif(isinstance(assignment, Increment)):
                        f.write('\t\t\t\t\t\t{} += 1;\n'.format(assignment.variable_name))
                    elif(isinstance(assignment, Decrement)):
                        f.write('\t\t\t\t\t\t{} -= 1;\n'.format(assignment.variable_name))
            f.write('\t\t\t\t}\n')
        f.write('''
    }

		if(commandIndex != -1) {
			memcpy_P(&tempCommand, &(m_command[commandIndex]), sizeof(Command));
			// Buttons
			if (tempCommand.button & A)
				ReportData->Button |= SWITCH_A;
			if (tempCommand.button & B)
				ReportData->Button |= SWITCH_B;
			if (tempCommand.button & X)
				ReportData->Button |= SWITCH_X;
			if (tempCommand.button & Y)
				ReportData->Button |= SWITCH_Y;
			if (tempCommand.button & L)
				ReportData->Button |= SWITCH_L;
			if (tempCommand.button & R)
				ReportData->Button |= SWITCH_R;
			if (tempCommand.button & ZL)
				ReportData->Button |= SWITCH_ZL;
			if (tempCommand.button & ZR)
				ReportData->Button |= SWITCH_ZR;
			if (tempCommand.button & PLUS)
				ReportData->Button |= SWITCH_PLUS;
			if (tempCommand.button & MINUS)
				ReportData->Button |= SWITCH_MINUS;
			if (tempCommand.button & HOME)
				ReportData->Button |= SWITCH_HOME;
			if (tempCommand.button & CAPTURE)
				ReportData->Button |= SWITCH_CAPTURE;
			if (tempCommand.button & LCLICK)
				ReportData->Button |= SWITCH_LCLICK;
			if (tempCommand.button & RCLICK)
				ReportData->Button |= SWITCH_RCLICK;

			// ASpam
			if (tempCommand.button & A_SPAM)
			{
				// Hold button for SPAM_DURATION, nothing for SPAM_DURATION
				if ((durationCount / SPAM_DURATION) % 2 == 0)
				{
					ReportData->Button |= SWITCH_A;
				}
			}

			// BSpam
			if (tempCommand.button & B_SPAM)
			{
				// Hold button for SPAM_DURATION, nothing for SPAM_DURATION
				if ((durationCount / SPAM_DURATION) % 2 == 0)
				{
					ReportData->Button |= SWITCH_B;
				}
			}

			// DPad
			bool up, down, left, right;
			up = (tempCommand.button & DPAD_UP);
			down = (tempCommand.button & DPAD_DOWN);
			left = (tempCommand.button & DPAD_LEFT);
			right = (tempCommand.button & DPAD_RIGHT);
			if (up)
			{
				ReportData->HAT = HAT_TOP;
				if (left)
				{
					ReportData->HAT = HAT_TOP_LEFT;
				}
				else if (right)
				{
					ReportData->HAT = HAT_TOP_RIGHT;
				}
			}
			else if (down)
			{
				ReportData->HAT = HAT_BOTTOM;
				if (left)
				{
					ReportData->HAT = HAT_BOTTOM_LEFT;
				}
				else if (right)
				{
					ReportData->HAT = HAT_BOTTOM_RIGHT;
				}
			}
			else if (left)
			{
				ReportData->HAT = HAT_LEFT;
			}
			else if (right)
			{
				ReportData->HAT = HAT_RIGHT;
			}

			// L-Stick
			up = (tempCommand.button & UP);
			down = (tempCommand.button & DOWN);
			left = (tempCommand.button & LEFT);
			right = (tempCommand.button & RIGHT);
			if (up)
			{
				ReportData->LY = STICK_MIN;
			}
			else if (down)
			{
				ReportData->LY = STICK_MAX;
			}
			if (left)
			{
				ReportData->LX = STICK_MIN;
			}
			else if (right)
			{
				ReportData->LX = STICK_MAX;
			}

			// R-Stick
			up = (tempCommand.button & RUP);
			down = (tempCommand.button & RDOWN);
			left = (tempCommand.button & RLEFT);
			right = (tempCommand.button & RRIGHT);
			if (up)
			{
				ReportData->RY = STICK_MIN;
			}
			else if (down)
			{
				ReportData->RY = STICK_MAX;
			}
			if (left)
			{
				ReportData->RX = STICK_MIN;
			}
			else if (right)
			{
				ReportData->RX = STICK_MAX;
			}

			durationCount++;

			if (durationCount >= tempCommand.duration)
			{
				commandIndex++;
				durationCount = 0;

				// We reached the end of a command sequence
				if (commandIndex > m_endIndex)
				{
					commandIndex = -1;
				}
			}
	}

		break;

	case DONE: return;
}

// Prepare to echo this report
memcpy(&last_report, ReportData, sizeof(USB_JoystickReport_Input_t));
echoes = ECHOES;
}
''')


def generate_code(name, program):
    new_directory = "./{}/".format(name)
    if not os.path.exists(new_directory):
        os.mkdir(new_directory)
    generate_config(new_directory, program.config_variables)
    generate_commands(new_directory, program.blocks[0].command_range[1], program.commands)
    generate_c_file(name, new_directory, program.variables, program.blocks)
