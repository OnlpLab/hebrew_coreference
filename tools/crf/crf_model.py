from transformers import BertPreTrainedModel, BertModel
from transformers.modeling_outputs import TokenClassifierOutput
from torch import nn
from torch.nn import CrossEntropyLoss
import torch.nn.functional as F


import torch
from torchcrf import CRF

from allencrf.conditional_random_field import ConditionalRandomField
log_soft = F.log_softmax

class BertForTokenClassification(BertPreTrainedModel):

    _keys_to_ignore_on_load_unexpected = ["pooler"]

    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.bert = BertModel(config, add_pooling_layer=False)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)

        self.init_weights()

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            head_mask=None,
            inputs_embeds=None,
            labels=None,
            output_attentions=None,
            output_hidden_states=None,
            return_dict=None,
    ):
        r"""
        labels (:obj:`torch.LongTensor` of shape :obj:`(batch_size, sequence_length)`, `optional`):
            Labels for computing the token classification loss. Indices should be in ``[0, ..., config.num_labels -
            1]``.
        """
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]

        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)

        loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()
            # Only keep active parts of the loss
            if attention_mask is not None:
                active_loss = attention_mask.view(-1) == 1
                active_logits = logits.view(-1, self.num_labels)
                active_labels = torch.where(
                    active_loss, labels.view(-1), torch.tensor(loss_fct.ignore_index).type_as(labels)
                )
                loss = loss_fct(active_logits, active_labels)
            else:
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return TokenClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )

import torch.nn.functional as F


# class BertCRF(BertPreTrainedModel):
#
#     def __init__(self, config):
#         super().__init__(config)
#         self.num_labels = config.num_labels
#         self.bert = BertModel(config)
#         self.dropout = nn.Dropout(config.hidden_dropout_prob)
#         self.classifier = nn.Linear(config.hidden_size, config.num_labels)
#         self.crf = CRF(self.num_labels, batch_first=True)
#
#         # self.crf = ConditionalRandomField(config.num_labels, include_start_end_transitions=False)
#         self.init_weights()
#
#     def forward(
#             self,
#             input_ids=None,
#             attention_mask=None,
#             token_type_ids=None,
#             position_ids=None,
#             head_mask=None,
#             inputs_embeds=None,
#             labels=None,
#             output_attentions=None,
#             output_hidden_states=None,
#             return_dict=None,
#     ):
#         r"""
#         labels (:obj:`torch.LongTensor` of shape :obj:`(batch_size, sequence_length)`, `optional`):
#             Labels for computing the token classification loss. Indices should be in ``[0, ..., config.num_labels -
#             1]``.
#         """
#         # return_dict = return_dict if return_dict is not None else self.config.use_return_dict
#         #
#         # outputs = self.bert(
#         #     input_ids,
#         #     attention_mask=attention_mask,
#         #     token_type_ids=token_type_ids,
#         #     position_ids=position_ids,
#         #     head_mask=head_mask,
#         #     inputs_embeds=inputs_embeds,
#         #     output_attentions=output_attentions,
#         #     output_hidden_states=output_hidden_states,
#         #     return_dict=return_dict,
#         # )
#         #
#         # sequence_output = outputs[0]
#         # sequence_output = self.dropout(sequence_output)
#         # logits = self.classifier(sequence_output)
#         # masks = torch.ones_like(labels, dtype=torch.uint8)
#         # loss = None
#         # if labels is not None:
#         #
#         #     log_likelihood, tags = self.crf(logits, labels, masks), self.crf.viterbi_tags(logits, masks)
#         #
#         #     loss = 0 - log_likelihood
#         # else:
#         #     tags = self.crf.decode(logits)
#         # tags = torch.Tensor(tags)
#         #
#         # if not return_dict:
#         #     output = (tags,) + outputs[2:]
#         #     return ((loss,) + output) if loss is not None else output
#         #
#         # return loss, tags
#
#
#         outputs = self.bert(input_ids, attention_mask)
#         sequence_output = outputs[0]
#         sequence_output = self.dropout(sequence_output)
#         emission = self.classifier(sequence_output)
#         to_mask = labels == -100
#         attn_masks2 = labels.clone()
#         attn_masks2[to_mask] = 0
#         attn_masks2[~to_mask] = 1
#         attn_masks2 = attn_masks2.type(torch.uint8)
#         labels[to_mask] = 0
#         if labels is not None:
#             loss = -self.crf(log_soft(emission, 2), labels, mask=attn_masks2, reduction='mean')
#             return loss, loss
#         else:
#             prediction = self.crf.decode(emission, mask=attn_masks2)
#             return prediction




class BERT_BiLSTM_CRF(BertPreTrainedModel):

    def __init__(self, config, need_birnn=True, rnn_dim=128):
        super(BERT_BiLSTM_CRF, self).__init__(config)

        self.num_tags = config.num_labels #for padding
        self.bert = BertModel(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        out_dim = config.hidden_size
        self.need_birnn = need_birnn


        if need_birnn:
            self.birnn = nn.LSTM(config.hidden_size, rnn_dim, num_layers=1, bidirectional=True, batch_first=True)
            out_dim = rnn_dim*2

        self.hidden2tag = nn.Linear(out_dim, config.num_labels)
        self.crf = CRF(config.num_labels, batch_first=True)

    def forward(
          self,
          input_ids=None,
          attention_mask=None,
          token_type_ids=None,
          position_ids=None,
          head_mask=None,
          inputs_embeds=None,
          labels=None,
          output_attentions=None,
          output_hidden_states=None,
          return_dict=None,
        ):
        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        sequence_output = outputs[0]

        emissions = self.tag_outputs(sequence_output)
        # print(labels)
        cond = labels != -100
        labels = labels.where(cond, torch.tensor(0,  device=labels.device))
        print(labels)
        print(attention_mask)
        loss = -1 * self.crf(emissions, labels, mask=attention_mask.byte())

        return loss, emissions


    def tag_outputs(self,sequence_output):

        if self.need_birnn:
            sequence_output, _ = self.birnn(sequence_output)

        sequence_output = self.dropout(sequence_output)
        emissions = self.hidden2tag(sequence_output)

        return emissions

    def predict(self, input_ids, token_type_ids=None, input_mask=None):
        emissions = self.tag_outputs(input_ids, token_type_ids, input_mask)
        return self.crf.decode(emissions, input_mask.byte())
