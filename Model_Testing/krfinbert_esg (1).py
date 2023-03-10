# -*- coding: utf-8 -*-
"""krfinbert_esg.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_cVBwxsa7LcHzjzCcS4l1ds0wxNPQrjm
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
import numpy as np

import warnings
warnings.filterwarnings('ignore') # to avoid warnings

import random
import pandas as pd
from tqdm import tqdm
import seaborn as sns
import matplotlib.pyplot as plt

"""
Sklearn Libraries
"""
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

"""
Transformer Libraries
"""
!pip install transformers
from transformers import BertTokenizer,  AutoModelForSequenceClassification, AdamW, get_linear_schedule_with_warmup

"""
Pytorch Libraries
"""
import torch
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler, TensorDataset

esg_data = pd.read_csv("/content/drive/MyDrive/kpmg_personal/concat.csv", 
                             encoding='utf-8')

esg_data

plt.figure(figsize = (15,8))

sns.set(style='darkgrid')
    
# Increase information on the figure
sns.set(font_scale=1.3)
sns.countplot(x='category', data = esg_data)
plt.title('ESG Category Distribution')
plt.xlabel('E,S,G,N')
plt.ylabel('Number of Contents')

def show_random_contents(total_number, df):
    
    # Get the random number of reviews
    n_contents = df.sample(total_number)
    
    # Print each one of the reviews
    for val in list(n_contents.index):
        print("Contents #°{}".format(val))
        print(" - Category: {}".format(df.iloc[val]["category"]))
        print(" - Contents: {}".format(df.iloc[val]["contents"]))
        print("")
        
# Show 5 random headlines
show_random_contents(5, esg_data)

def encode_categories_values(df):
    
    possible_categories = df.category.unique()
    category_dict = {}
    
    for index, possible_category in enumerate(possible_categories):
        category_dict[possible_category] = index
    
    # Encode all the sentiment values
    df['label'] = df.category.replace(category_dict)
    
    return df, category_dict
 
# Perform the encoding task on the data set
esg_data, category_dict = encode_categories_values(esg_data)

X_train,X_val, y_train, y_val = train_test_split(esg_data.index.values, 
                                                  esg_data.label.values, 
                                                  test_size = 0.15, 
                                                  random_state = 2022, 
                                                  stratify = esg_data.label.values)

esg_data.loc[X_train, 'data_type'] = 'train'
esg_data.loc[X_val, 'data_type'] = 'val'

# Vizualiez the number of sentiment occurence on each type of data
esg_data.groupby(['category', 'label', 'data_type']).count()

# Get the FinBERT Tokenizer
finbert_tokenizer = BertTokenizer.from_pretrained('snunlp/KR-FinBert-SC', 
                                          do_lower_case=True)

def get_contents_len(df):
    
    contents_sequence_lengths = []
    
    print("Encoding in progress...")
    for content in tqdm(df.contents):
        encoded_content = finbert_tokenizer.encode(content, 
                                         add_special_tokens = True)
        
        # record the length of the encoded review
        contents_sequence_lengths.append(len(encoded_content))
    print("End of Task.")
    
    return contents_sequence_lengths

def show_contents_distribution(sequence_lengths, figsize = (15,8)):
    
    # Get the percentage of reviews with length > 512
    len_512_plus = [rev_len for rev_len in sequence_lengths if rev_len > 512]
    percent = (len(len_512_plus)/len(sequence_lengths))*100
    
    print("Maximum Sequence Length is {}".format(max(sequence_lengths)))
    
    # Configure the plot size
    plt.figure(figsize = figsize)

    sns.set(style='darkgrid')
    
    # Increase information on the figure
    sns.set(font_scale=1.3)
    
    # Plot the result
    sns.distplot(sequence_lengths, kde = False, rug = False)
    plt.title('Contents Lengths Distribution')
    plt.xlabel('Contents Length')
    plt.ylabel('Number of Contents')

show_contents_distribution(get_contents_len(esg_data))

# Encode the Training and Validation Data
encoded_data_train = finbert_tokenizer.batch_encode_plus(
    esg_data[esg_data.data_type=='train'].contents.values, 
    return_tensors='pt',
    add_special_tokens=True, 
    return_attention_mask=True, 
    pad_to_max_length=True, 
    max_length=200 # the maximum lenght observed in the headlines
)

encoded_data_val = finbert_tokenizer.batch_encode_plus(
    esg_data[esg_data.data_type=='val'].contents.values, 
    return_tensors='pt',
    add_special_tokens=True, 
    return_attention_mask=True, 
    pad_to_max_length=True, 
    max_length=200 # the maximum length observed in the headlines
)


input_ids_train = encoded_data_train['input_ids']
attention_masks_train = encoded_data_train['attention_mask']
labels_train = torch.tensor(esg_data[esg_data.data_type=='train'].label.values)

input_ids_val = encoded_data_val['input_ids']
attention_masks_val = encoded_data_val['attention_mask']
sentiments_val = torch.tensor(esg_data[esg_data.data_type=='val'].label.values)


dataset_train = TensorDataset(input_ids_train, attention_masks_train, labels_train)
dataset_val = TensorDataset(input_ids_val, attention_masks_val, sentiments_val)

model = AutoModelForSequenceClassification.from_pretrained("snunlp/KR-FinBert-SC",
                                                          num_labels=len(category_dict),
                                                          output_attentions=False,
                                                          output_hidden_states=False,
                                                           ignore_mismatched_sizes=True)

batch_size = 5

dataloader_train = DataLoader(dataset_train, 
                              sampler=RandomSampler(dataset_train), 
                              batch_size=batch_size)

dataloader_validation = DataLoader(dataset_val, 
                                   sampler=SequentialSampler(dataset_val), 
                                   batch_size=batch_size)

optimizer = AdamW(model.parameters(),
                  lr=1e-5, 
                  eps=1e-8)

epochs = 5

scheduler = get_linear_schedule_with_warmup(optimizer, 
                                            num_warmup_steps=0,
                                            num_training_steps=len(dataloader_train)*epochs)

def f1_score_func(preds, labels):
    preds_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return f1_score(labels_flat, preds_flat, average='weighted')

def accuracy_per_class(preds, labels):
    label_dict_inverse = {v: k for k, v in category_dict.items()}
    
    preds_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()

    for label in np.unique(labels_flat):
        y_preds = preds_flat[labels_flat==label]
        y_true = labels_flat[labels_flat==label]
        print(f'Class: {label_dict_inverse[label]}')
        print(f'Accuracy: {len(y_preds[y_preds==label])}/{len(y_true)}\n')

seed_val = 2022
random.seed(seed_val)
np.random.seed(seed_val)
torch.manual_seed(seed_val)
torch.cuda.manual_seed_all(seed_val)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)


def evaluate(dataloader_val):

    model.eval()
    
    loss_val_total = 0
    predictions, true_vals = [], []
    
    for batch in dataloader_val:
        
        batch = tuple(b.to(device) for b in batch)
        
        inputs = {'input_ids':      batch[0],
                  'attention_mask': batch[1],
                  'labels':         batch[2],
                 }

        with torch.no_grad():        
            outputs = model(**inputs)
            
        loss = outputs[0]
        logits = outputs[1]
        loss_val_total += loss.item()

        logits = logits.detach().cpu().numpy()
        label_ids = inputs['labels'].cpu().numpy()
        predictions.append(logits)
        true_vals.append(label_ids)
    
    loss_val_avg = loss_val_total/len(dataloader_val) 
    
    predictions = np.concatenate(predictions, axis=0)
    true_vals = np.concatenate(true_vals, axis=0)
            
    return loss_val_avg, predictions, true_vals


for epoch in tqdm(range(1, epochs+1)):
    
    model.train()
    
    loss_train_total = 0

    progress_bar = tqdm(dataloader_train, desc='Epoch {:1d}'.format(epoch), leave=False, disable=False)
    for batch in progress_bar:

        model.zero_grad()
        
        batch = tuple(b.to(device) for b in batch)
        
        inputs = {'input_ids':      batch[0],
                  'attention_mask': batch[1],
                  'labels':         batch[2],
                 }       

        outputs = model(**inputs)
        
        loss = outputs[0]
        loss_train_total += loss.item()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()
        scheduler.step()
        
        progress_bar.set_postfix({'training_loss': '{:.3f}'.format(loss.item()/len(batch))})
         
    torch.save(model.state_dict(), f'finetuned_finBERT_epoch_{epoch}.model')
        
    tqdm.write(f'\nEpoch {epoch}')
    
    loss_train_avg = loss_train_total/len(dataloader_train)            
    tqdm.write(f'Training loss: {loss_train_avg}')
    
    val_loss, predictions, true_vals = evaluate(dataloader_validation)
    val_f1 = f1_score_func(predictions, true_vals)
    tqdm.write(f'Validation loss: {val_loss}')
    tqdm.write(f'F1 Score (Weighted): {val_f1}')

model = AutoModelForSequenceClassification.from_pretrained("snunlp/KR-FinBert-SC",
                                                          num_labels=len(category_dict),
                                                          output_attentions=False,
                                                          output_hidden_states=False,
                                                           ignore_mismatched_sizes=True)

model.to(device)

model.load_state_dict(torch.load('finetuned_finBERT_epoch_4.model', 
                                 map_location=torch.device('cpu')))

_, predictions, true_vals = evaluate(dataloader_validation)

accuracy_per_class(predictions, true_vals)

# max_length = 200





























