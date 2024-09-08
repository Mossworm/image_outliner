import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter, ImageChops
import numpy as np
import os

class ImageOutliner:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 아웃라인 생성기")
        self.root.geometry("800x600")

        self.images = []
        self.thumbnail_size = (100, 100)
        self.main_thumbnail_size = (300, 300)

        # 메인 프레임
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 왼쪽 프레임 (컨트롤)
        left_frame = tk.Frame(main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.thickness_label = tk.Label(left_frame, text="아웃라인 굵기 (0-40):")
        self.thickness_label.pack()

        self.thickness_var = tk.StringVar()
        self.thickness_var.set("5")
        self.thickness_entry = tk.Entry(left_frame, textvariable=self.thickness_var, width=5)
        self.thickness_entry.pack()

        self.update_button = tk.Button(left_frame, text="아웃라인 업데이트", command=self.update_outlines)
        self.update_button.pack(pady=5)

        self.load_button = tk.Button(left_frame, text="이미지 불러오기", command=self.load_images)
        self.load_button.pack(pady=5)

        self.save_button = tk.Button(left_frame, text="이미지 저장", command=self.save_images)
        self.save_button.pack(pady=5)

        # 수직 구분선 추가
        separator = ttk.Separator(main_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 오른쪽 프레임 (이미지 표시)
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 메인 썸네일과 정보를 포함할 프레임
        main_info_frame = tk.Frame(right_frame)
        main_info_frame.pack(fill=tk.X, pady=10)

        # 메인 썸네일 (테두리 추가)
        self.main_canvas = tk.Canvas(main_info_frame, width=310, height=310, bd=2, relief=tk.SUNKEN)
        self.main_canvas.pack(side=tk.LEFT, padx=(0, 10))

        # 파일 정보를 표시할 프레임
        info_frame = tk.Frame(main_info_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 파일 정보를 중앙에 배치하기 위한 추가 프레임
        center_frame = tk.Frame(info_frame)
        center_frame.pack(expand=True)

        self.filename_label = tk.Label(center_frame, text="", wraplength=200, justify=tk.LEFT, anchor="w")
        self.filename_label.pack(fill=tk.X)

        self.size_label = tk.Label(center_frame, text="", anchor="w")
        self.size_label.pack(fill=tk.X)

        # 썸네일 그리드 (스크롤 가능)
        self.thumbnail_canvas = tk.Canvas(right_frame)
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.thumbnail_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.thumbnail_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.thumbnail_canvas.bind('<Configure>', lambda e: self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all")))

        self.thumbnail_frame = tk.Frame(self.thumbnail_canvas)
        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_frame, anchor="nw")

        # 마우스 휠 이벤트 바인딩
        self.thumbnail_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.thumbnail_frame.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_images(self):
        file_paths = filedialog.askopenfilenames()
        if file_paths:
            self.images = [{"path": path, "image": Image.open(path), "outlined": None} for path in file_paths]
            self.update_outlines()
            self.display_thumbnails()

    def update_outlines(self):
        try:
            thickness = int(self.thickness_var.get())
            if thickness < 0 or thickness > 40:
                raise ValueError("굵기는 0에서 40 사이여야 합니다.")
            for img in self.images:
                if thickness == 0:
                    img["outlined"] = img["image"].copy()
                else:
                    img["outlined"] = self.add_outline(img["image"], thickness)
            self.display_thumbnails()
        except ValueError as e:
            messagebox.showerror("오류", str(e))

    def display_thumbnails(self):
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()

        for i, img in enumerate(self.images):
            thumbnail = img["outlined"].copy() if img["outlined"] else img["image"].copy()
            thumbnail.thumbnail(self.thumbnail_size)
            photo = ImageTk.PhotoImage(thumbnail)
            
            button = tk.Button(self.thumbnail_frame, image=photo, command=lambda idx=i: self.display_main_thumbnail(idx))
            button.image = photo
            button.grid(row=i//5, column=i%5, padx=5, pady=5)
            
            # 각 썸네일 버튼에 마우스 휠 이벤트 바인딩
            button.bind("<MouseWheel>", self._on_thumbnail_mousewheel)

        if self.images:
            self.display_main_thumbnail(0)

        # 스크롤 영역 업데이트
        self.thumbnail_canvas.update_idletasks()
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))

    def _on_thumbnail_mousewheel(self, event):
        # 이벤트를 상위 위젯으로 전파
        self.thumbnail_canvas.event_generate("<MouseWheel>", delta=event.delta, state=event.state)
        return "break"  # 이벤트 처리 중단

    def display_main_thumbnail(self, index):
        img = self.images[index]["outlined"] if self.images[index]["outlined"] else self.images[index]["image"]
        thumbnail = img.copy()
        thumbnail.thumbnail(self.main_thumbnail_size)
        
        background = Image.new('RGBA', self.main_thumbnail_size, (240, 240, 240, 255))
        offset = ((self.main_thumbnail_size[0] - thumbnail.width) // 2,
                  (self.main_thumbnail_size[1] - thumbnail.height) // 2)
        background.paste(thumbnail, offset, thumbnail)
        
        self.main_photo = ImageTk.PhotoImage(background)
        self.main_canvas.delete("all")
        self.main_canvas.create_image(155, 155, anchor=tk.CENTER, image=self.main_photo)

        # 파일 정보 업데이트
        filename = os.path.basename(self.images[index]["path"])
        self.filename_label.config(text=f"파일명: {filename}")
        
        original_size = self.images[index]["image"].size
        self.size_label.config(text=f"크기: {original_size[0]}x{original_size[1]}")

    def add_outline(self, image, thickness):
        if thickness == 0:
            return image.copy()
        
        # 이미지를 RGBA 모드로 변환
        image = image.convert("RGBA")
        
        # 알파 채널 추출
        alpha = image.split()[3]
        
        # NumPy 배열로 변환
        alpha_array = np.array(alpha)
        
        # 커널 생성 (항상 홀수 크기가 되도록 조정)
        kernel_size = thickness * 2 + 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        
        # 팽창 연산
        dilated = Image.fromarray(self.dilate(alpha_array, kernel))
        
        # 원본 마스크와 확장된 마스크의 차이로 아웃라인 영역 생성
        outline_mask = ImageChops.difference(dilated, alpha)
        
        # 아웃라인 이미지 생성 (선명한 검은색)
        outline = Image.new('RGBA', image.size, (0, 0, 0, 0))
        outline_draw = ImageDraw.Draw(outline)
        outline_draw.bitmap((0, 0), outline_mask, fill=(0, 0, 0, 255))
        
        # 원본 이미지와 아웃라인 합성
        result = Image.alpha_composite(outline, image)
        
        return result

    def dilate(self, image, kernel):
        h, w = image.shape
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        
        padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        
        # 효율적인 NumPy 연산 사용
        windows = np.lib.stride_tricks.sliding_window_view(padded, (kh, kw))
        dilated = np.max(windows * kernel, axis=(2, 3))
        
        return dilated.astype(np.uint8)

    def save_images(self):
        if not self.images:
            messagebox.showinfo("알림", "저장할 이미지가 없습니다.")
            return
        
        save_dir = filedialog.askdirectory()
        if save_dir:
            for img in self.images:
                if img["outlined"]:
                    base_name = os.path.basename(img["path"])
                    name, ext = os.path.splitext(base_name)
                    save_path = os.path.join(save_dir, f"{name}_outlined{ext}")
                    img["outlined"].save(save_path)
            messagebox.showinfo("완료", f"{len(self.images)}개의 이미지가 저장되었습니다.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOutliner(root)
    root.mainloop()