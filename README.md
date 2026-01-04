You need the free file sync tool:

https://freefilesync.org/


Also you need to create the folders on hoer hard drive:

# Folder for pictures from camera:
INPUT_DIR = r"C:\Photo_booth\new_images"

# Folder for finished and framed pictures:
OUTPUT_DIR = r"C:\Photo_booth\output_folder"

# Frame File:
FRAME_PATH = r"C:\Photo_booth\frames\example.png"      <-- a frame file is also needed. Just Use anything you like with a transparent channel / middle part

And change the mtp path in the ffs batch file 

    <FolderPairs>
        <Pair>
            <Left>mtp:\D5200\Wechselmedien\DCIM\103LLT25</Left>                    <<---- According to your camera
            <Right>C:\Photo_booth\new_images</Right>
        </Pair>
