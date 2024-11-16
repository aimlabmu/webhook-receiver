from django.db import migrations, models
import django.db.models.deletion
from django_fsm import FSMIntegerField

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('webhook_receiver', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OmiseOrder',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False, editable=False)),
                ('email', models.EmailField(max_length=254)),
                ('first_name', models.CharField(max_length=254)),
                ('last_name', models.CharField(max_length=254)),
                ('received', models.DateTimeField(auto_now_add=True)),
                ('status', FSMIntegerField(choices=[(0, 'New'), (1, 'Processing'), (2, 'Processed'), (-1, 'Error')], default=0, protected=True)),
                ('webhook', models.ForeignKey(to='webhook_receiver.JSONWebhookData', null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'app_label': 'webhook_receiver_omise',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OmiseOrderItem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('course_id', models.CharField(max_length=254)),
                ('email', models.EmailField(max_length=254)),
                ('status', FSMIntegerField(choices=[(0, 'New'), (1, 'Processing'), (2, 'Processed'), (-1, 'Error')], default=0, protected=True)),
                ('order', models.ForeignKey(to='webhook_receiver_omise.OmiseOrder', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'app_label': 'webhook_receiver_omise',
                'constraints': [
                    models.UniqueConstraint(fields=['order', 'course_id', 'email'], name='unique_omise_order_courseid_email'),
                ],
            },
            bases=(models.Model,),
        ),
    ]