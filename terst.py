import torch
import cv2


def load_model():
    # Загрузка предобученной модели YOLOv5
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    return model


def is_object_present(image_path: str, model) -> bool:
    # Загрузка изображения
    img = cv2.imread(image_path)

    # Использование модели для детектирования объектов на изображении
    results = model(img)

    # Получение меток объектов
    detected_classes = [model.names[int(c)] for c in results.xyxyn[0][:, -1]]
    print(f"Detected classes in {image_path}: {detected_classes}")

    # Проверка на наличие класса "bottle"
    if 'bottle' in detected_classes:
        return True

    return False


def find_object_in_images(reference_image_path: str, other_image_paths: list):
    # Загрузка модели
    model = load_model()

    # Проверка эталонного изображения
    if not is_object_present(reference_image_path, model):
        print("Эталонный объект не найден на эталонном изображении.")
        return

    # Поиск объекта на других изображениях
    for image_path in other_image_paths:
        if is_object_present(image_path, model):
            print(f"Объект найден на изображении: {image_path}")
        else:
            print(f"Объект не найден на изображении: {image_path}")


# Пример использования
reference_image_path = "test.jpg"  # путь к эталонному изображению
other_image_paths = ["test1.jpg", "test2.jpg", "test3.jpg", "test4.jpg"]  # пути к другим изображениям

find_object_in_images(reference_image_path, other_image_paths)
