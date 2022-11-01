---
title: Publish the application

---


# Publish the trac app

To publish the trac app, and make it usable by other users, we need to start the TRAC UI and Runtime first.

```bash
cd trac-ui/

python manage.py migrate
python manage.py runserver 0.0.0.0:5000
```

This will start the UI server on `localhost:5000`.

Then publishing the app with

```bash
trac-cli publish \
    --image-name vrp-algo \
    --endpoint http://localhost:5000 \
    --name 'A vehicle routing algorithm app' \
    --description 'An app helps to route vehicles'
```

In the returned result, we will get an URL that links to the dashboard for the published app, e.g., `http://localhost:5000/instances/2/dashboard/`.
