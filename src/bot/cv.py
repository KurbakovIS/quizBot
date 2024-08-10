import torch
import cv2


def load_model():
    # Загрузка предобученной модели YOLOv5
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    return model


def is_duck_present(user_image_path: str, reference_image_path: str, model) -> bool:
    # Загрузка изображения пользователя
    user_image = cv2.imread(user_image_path)

    # Загрузка эталонного изображения (например, утки)
    reference_image = cv2.imread(reference_image_path)

    # Использование модели для детектирования объектов на изображениях
    results_user = model(user_image)
    results_reference = model(reference_image)

    # Получение меток объектов
    labels_user = results_user.xyxyn[0][:, -1].numpy()
    labels_reference = results_reference.xyxyn[0][:, -1].numpy()

    # Получение имен классов
    class_names = results_user.names

    # Проверка на наличие совпадающего объекта на обоих изображениях
    for label in labels_user:
        if class_names[int(label)] in class_names[int(labels_reference[0])]:  # Совпадение метки объекта
            return True

    return False


# Загрузка модели
# model = load_model()
#
# # Проверка изображения
# result = is_duck_present('user_photo.jpg', model)
# if result:
#     print("Утка найдена!")
# else:
#     print("Утка не найдена.")
