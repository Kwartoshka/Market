FROM python:3.8
COPY ./ /Diplom
WORKDIR /Diplom
RUN pip install -r /Diplom/requirements.txt
# RUN python /Diplom/shop/manage.py migrate
CMD ["python", "shop/manage.py", "runserver", "0.0.0.0:8000"]
