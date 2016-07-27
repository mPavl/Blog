from Tkinter import Tk, Button, Label, IntVar, Entry
from tkFileDialog import askopenfilename, asksaveasfilename   
from PIL import Image, ImageTk

root = Tk()
root.title("Image") 
but = Button(root)

image = Image.open(askopenfilename())
photo = ImageTk.PhotoImage(image)
label = Label(root, image=photo)
label.pack()

var=IntVar()
left_but = Entry(root, width = 20, text="Left")
upper_but = Entry(root, width = 20, text="Upper")
right_but = Entry(root, width = 20, text="Right")
lower_but = Entry(root, width = 20, text="Lower")
left_but.pack(), upper_but.pack(), right_but.pack(), lower_but.pack()
left_but = var.get() 
upper_but = var.get() 
right_but = var.get() 
lower_but = var.get()
but1 = Button(root,text="Resize")
but2 = Button(root,text="Crop")
but1.pack(), but2.pack()
box1 = (left_but, upper_but)
box2 = (left_but, upper_but, right_but, lower_but)

def re(event):
	try:
		save_as = asksaveasfilename()		
		resize_event = image.resize(box1).save(save_as, 'JPEG')
        	resize_event.close()
	except:
		print("Error: Can't extend outside image")
			
def cr(event):
	try:
		save_as = asksaveasfilename()		
		crop_event = image.crop(box2).save(save_as, 'JPEG')
        	crop_event.close()
	except:
		print("Error: Can't extend outside image")	

but1.bind('<Button-1>', re)
but2.bind('<Button-1>', cr)

root.mainloop()
