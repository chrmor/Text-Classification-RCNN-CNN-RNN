import torch 
import torch.autograd as autograd
import torch.nn as nn
import modelsio

def train(train_loader, dev_loader, model, cuda, learnign_rate, num_epochs, batch_size, log_file, model_name, early_stop=False, patience = 1):

	with open(log_file, 'a') as the_file:
		the_file.write("\nModel: " + str(model))
		the_file.write("\nLearning rate: " + str(learnign_rate));
		the_file.write("\nEpochs: " + str(num_epochs));
		the_file.write("\nTraining started...");        
		the_file.close()
    
    # gpu runnable 
	if cuda: 
		model.cuda()

	#Parallel
	#torch.nn.DataParallel(model)
        
    # train mode 
	model.train()

	num_batch = len(train_loader)
	step = 0

	#Loss and optimizer 
	criterion = nn.CrossEntropyLoss()
	optimizer = torch.optim.Adam(model.parameters(), lr = learnign_rate)

	stop = False
	max_accuracy_on_dev_set = 0.0
    
	for epoch in range(num_epochs):
		if early_stop and stop:
			continue        
		for i, batch in enumerate(train_loader):
			if early_stop and stop:
				continue    
			feature, target = batch.text, batch.label
			if feature.size()[0]!= batch_size:
				continue
			target.data.sub_(1)  # index 
			if cuda:
				feature, target = feature.cuda(), target.cuda()
			#if feature.size()[1] < 5:
			#	continue 

			#Forward, Backward, Optimize 
			optimizer.zero_grad()
			output = model(feature)
			#_, predicted = torch.max(output, 1)
			loss = criterion(output, target)
			loss.backward()
			nn.utils.clip_grad_norm_(model.parameters(), 3, norm_type = 2) # l2 constraint of 3

			optimizer.step()

			step += 1 



			if(step) % 100 == 0:
				msg = 'Epoch [%d/%d], Steps [%d/%d], Loss: %.4f' % (epoch+1, num_epochs, step,  num_batch * num_epochs, loss.item())
				print(msg)
				with open(log_file, 'a') as the_file:
					the_file.write('\n' + msg)
					the_file.close()

		if True: #Do this at each epoch
			msg, accuracy = eval(dev_loader, model, cuda, False)
			print(msg)
			with open(log_file, 'a') as the_file:
				the_file.write('\nDev: ' + msg)
				the_file.close()
			if max_accuracy_on_dev_set <= accuracy:
				max_accuracy_on_dev_set = accuracy
				modelsio.save_model(model, model_name + "_best")
				stop = False
				epochs_stop = patience
			else:
				epochs_stop -= 1
				if epochs_stop == 0:
					stop = True
                
	with open(log_file, 'a') as the_file:
		the_file.write("\nTraining finished...");                

def eval_treshold(test_loader, model, cuda, print_details, th):
 	#eval mode 
 	model.eval()

 	#Loss and optimizer 
 	criterion = nn.CrossEntropyLoss()

 	corrects = 0
 	predictions = 0
 	avg_loss = 0 
 	with torch.no_grad(): 
 		for i, batch in enumerate(test_loader):
 			feature, target = batch.text, batch.label
 			#print("Batch: " + str(feature.size()) )            
 			target.data.sub_(1) # index
 			if cuda:
 				feature, target = feature.cuda(), target.cuda()
    
 			output = model(feature)
 			#loss = criterion(output, target) # losses are summed, not average 

 			prediction = torch.max(output, 1)[1].view(target.size()).data
 			th_output = (torch.max(output, 1)[0] >= th)
            
 			th_prediction = []
 			th_target = []
 			ix = 0;
 			for item in th_output.data:
 				if item == 1:
 					th_prediction.append(prediction.data[ix].item())
 					th_target.append(target.data[ix].item())
 					predictions += 1;
 				ix += 1
            
 			corrects += (torch.tensor(th_prediction) == torch.tensor(th_target)).sum()
            
 			if print_details:
 				#avg_loss += loss.item()
 				#print("MAX:" + str(torch.max(output, 1)[0]))
 				print("\nOutPut:\n" + str(output.data))
 				print("Target:\n" + str(target.data))
 				print("Prediction:\n" + str(prediction.data))
 				print("TH_Output:\n" + str(th_output.data))
 				#print("\nPrediction:\n" + str(torch.max(output, 1)))
 				print("Corrects:\n" + str(scores))
 				print("TH Prediction:\n" + str(th_prediction))
 				print("TH Target:\n" + str(th_target))
 				#avg_loss += loss.item()
            
            
 	
 	size = len(test_loader.dataset)
 	accuracy = 100 * float(corrects) / predictions 
 	model.train()
 	msg = '\nTH: {:.2f} Coverage: {:.2f}%({}/{}) Accuracy: {:.4f}%({}/{}) \n'.format(th, predictions/size, predictions, size, accuracy, corrects, predictions)
 	return msg 


def eval_treshold_classes(label_field, test_loader, model, cuda, print_details, th):
    
 	csv_rows = []
    
 	#eval mode 
 	model.eval()

 	#Loss and optimizer 
 	criterion = nn.CrossEntropyLoss()

 	predictions_per_class = {}
 	examples_per_class = {}
 	total_examples_per_class = {}    
 	corrects_per_class = {}
 	for label in label_field.vocab.itos[1:]:
 		predictions_per_class[label] = 0
 		corrects_per_class[label] = 0
 		examples_per_class[label] = 0
 		total_examples_per_class[label] = 0

    
 	corrects = 0
 	predictions = 0
 	avg_loss = 0 
 	with torch.no_grad(): 
 		for i, batch in enumerate(test_loader):
 			feature, target = batch.text, batch.label
 			#print("Batch: " + str(feature.size()) )            
 			target.data.sub_(1) # index
 			if cuda:
 				feature, target = feature.cuda(), target.cuda()
               
 			output = model(feature)
 			#loss = criterion(output, target) # losses are summed, not average 
 			if list(target.size())[0]==1:
 				print("batch size: " + str(target.size()))
 				continue
 			prediction = torch.max(output, 1)[1].view(target.size()).data
            
 			th_output = (torch.max(output, 1)[0] >= th)
            
 			th_prediction = []
 			th_target = []
 			ix = 0;
 			for item in th_output.data:
 				if item == 1:
 					th_prediction.append(prediction.data[ix].item())
 					th_target.append(target.data[ix].item())
 					predictions += 1
 				ix += 1
            
 			t_th_target = torch.tensor(th_target)
 			t_th_prediction = torch.tensor(th_prediction)
 			matches = (t_th_prediction == t_th_target)
 			scores = matches.sum()
 			corrects += scores            
            
 			for label in label_field.vocab.itos[1:]:
 				idx = label_field.vocab.stoi[label]-1
 				#print(label + " --> " + str(idx))
 				t_class_target = t_th_target.clone()
 				examples_per_class[label] += (t_class_target==idx).sum()
 				total_examples_per_class[label] += (target==idx).sum()                
 				t_class_target[t_class_target!=idx] = -1
 				corrects_per_class[label] += (torch.tensor(th_prediction) == t_class_target).sum()
            
 			if print_details:
 				#avg_loss += loss.item()
 				#print("MAX:" + str(torch.max(output, 1)[0]))
 				print("\nOutPut:\n" + str(output.data))
 				print("Target:\n" + str(target))
 				print("Prediction:\n" + str(prediction.data))                
 				print("Matches:\n" + str(matches.data))
 				print("TH_Output:\n" + str(th_output.data))
 				#print("\nPrediction:\n" + str(torch.max(output, 1)))
 				print("Corrects:\n" + str(scores))
 				print("TH Prediction:\n" + str(th_prediction))
 				print("TH Target:\n" + str(th_target))
 				print("Target class: " + str(t_class_target))                
 				print("Accuracy:\n")
 				for label in label_field.vocab.itos[1:]:
 					accuracy_class = 100 * float(corrects_per_class[label]) / examples_per_class[label]
 					print(label + ": " + str(accuracy_class))
            
 	size = len(test_loader.dataset)
 	accuracy = 100 * float(corrects) / predictions 
 	coverage = predictions/size
 	model.train()
    
 	csv_row = [th, 'all', coverage, predictions, size, accuracy, corrects.item()]
 	csv_rows.append(csv_row)
    
 	msg = '\nTH: {:.2f} Coverage: {:.2f}({}/{})  Accuracy: {:.4f}({}/{}) \n'.format(th, coverage, predictions, size, accuracy, corrects, predictions)
 	dtl_msg = 'Classes:\n'
 	for label in label_field.vocab.itos[1:]:
 		if examples_per_class[label].item() == 0:
 			accuracy_class = 0
 		else:    
 			accuracy_class = 100 * float(corrects_per_class[label].item()) / examples_per_class[label].item()
 		#print(label + " : " + str(float(total_examples_per_class[label])))    
        
 		cl_coverage = float(examples_per_class[label].item())/float(total_examples_per_class[label])
 		cl_covered = examples_per_class[label].item()
 		cl_total = total_examples_per_class[label].item()
 		cl_correct = corrects_per_class[label].item()
 		csv_row = [th, label, cl_coverage, cl_covered, cl_total, accuracy_class, cl_correct]
 		csv_rows.append(csv_row)
        
 		dtl_msg += label + ": " + 'Coverage: {:.2f}({}/{})  Accuracy: {:.4f}({}/{}) \n'.format(cl_coverage, cl_covered, cl_total,  accuracy_class, cl_correct, cl_covered)
 	return msg + dtl_msg, csv_rows

def eval_combined_treshold_classes(label_field, test_loader, model1, model2, cuda, print_details, th):
 	#eval mode 
 	model.eval()

 	predictions_per_class = {}
 	examples_per_class = {}
 	total_examples_per_class = {}    
 	corrects_per_class = {}
 	for label in label_field.vocab.itos[1:]:
 		predictions_per_class[label] = 0
 		corrects_per_class[label] = 0
 		examples_per_class[label] = 0
 		total_examples_per_class[label] = 0

    
 	corrects = 0
 	predictions = 0
 	avg_loss = 0 
 	with torch.no_grad(): 
 		for i, batch in enumerate(test_loader):
 			feature, target = batch.text, batch.label
 			#print("Batch: " + str(feature.size()) )            
 			target.data.sub_(1) # index
 			if cuda:
 				feature, target = feature.cuda(), target.cuda()
               
 			output = model(feature)
 			if list(target.size())[0]==1:
 				print("batch size: " + str(target.size()))
 				continue
 			prediction = torch.max(output, 1)[1].view(target.size()).data
 			th_output = (torch.max(output, 1)[0] >= th)
            
 			th_prediction = []
 			th_target = []
 			ix = 0;
 			for item in th_output.data:
 				if item == 1:
 					th_prediction.append(prediction.data[ix].item())
 					th_target.append(target.data[ix].item())
 					predictions += 1
 				ix += 1
            
 			t_th_target = torch.tensor(th_target)
 			t_th_prediction = torch.tensor(th_prediction)
 			matches = (t_th_prediction == t_th_target)
 			scores = matches.sum()
 			corrects += scores            
            
 			for label in label_field.vocab.itos[1:]:
 				idx = label_field.vocab.stoi[label]-1
 				print(label + " --> " + str(idx))
 				t_class_target = t_th_target.clone()
 				examples_per_class[label] += (t_class_target==idx).sum()
 				total_examples_per_class[label] += (target==idx).sum()                
 				t_class_target[t_class_target!=idx] = -1
 				corrects_per_class[label] += (torch.tensor(th_prediction) == t_class_target).sum()
            
 			if print_details:
 				#avg_loss += loss.item()
 				#print("MAX:" + str(torch.max(output, 1)[0]))
 				print("\nOutPut:\n" + str(output.data))
 				print("Target:\n" + str(target))
 				print("Prediction:\n" + str(prediction.data))                
 				print("Matches:\n" + str(matches.data))
 				print("TH_Output:\n" + str(th_output.data))
 				#print("\nPrediction:\n" + str(torch.max(output, 1)))
 				print("Corrects:\n" + str(scores))
 				print("TH Prediction:\n" + str(th_prediction))
 				print("TH Target:\n" + str(th_target))
 				print("Target class: " + str(t_class_target))                
 				print("Accuracy:\n")
 				for label in label_field.vocab.itos[1:]:
 					accuracy_class = 100 * float(corrects_per_class[label]) / examples_per_class[label]
 					print(label + ": " + str(accuracy_class))
            
 	
 	size = len(test_loader.dataset)
 	accuracy = 100 * float(corrects) / predictions 
 	model.train()
 	msg = '\nTH: {:.2f} Recall: {:.2f}%({}/{})  Accuracy: {:.4f}%({}/{}) \n'.format(th, predictions/size, predictions, size, accuracy, corrects, predictions)
 	dtl_msg = '\nAccuracy per class:\n'
 	for label in label_field.vocab.itos[1:]:
 		if examples_per_class[label].item() == 0:
 			accuracy_class = 0
 		else:    
 			accuracy_class = 100 * float(corrects_per_class[label].item()) / examples_per_class[label].item()
 		dtl_msg += label + ": " + 'Recall: {:.2f}%({}/{})  Accuracy: {:.4f}%({}/{}) \n'.format(float(examples_per_class[label].item())/float(total_examples_per_class[label]), examples_per_class[label].item(), total_examples_per_class[label],  accuracy_class, corrects_per_class[label].item(), examples_per_class[label].item())
 	return msg + dtl_msg

def eval(test_loader, model, cuda, print_details):
 	#eval mode 
 	model.eval()

 	#Loss and optimizer 
 	criterion = nn.CrossEntropyLoss()

 	corrects = 0
 	avg_loss = 0 
 	with torch.no_grad(): 
 		for i, batch in enumerate(test_loader):
 			feature, target = batch.text, batch.label
 			#print("Batch: " + str(feature.size()) )            
 			target.data.sub_(1) # index
 			if cuda:
 				feature, target = feature.cuda(), target.cuda()
    
 			output = model(feature)
 			#loss = criterion(output, target) # losses are summed, not average 
 			if list(target.size())[0]==1:
 				print("batch size: " + str(target.size()))
 				continue
 			#avg_loss += loss.item()
 			scores = (torch.max(output, 1)[1].view(target.size()).data == target.data).sum()
 			corrects += scores
            
 			if print_details:
 				#avg_loss += loss.item()
 				print("\nOutPut:\n" + str(output))
 				print("Target:\n" + str(target.data))
 				print("Max:\n" + str(torch.max(output, 1)[1].view(target.size()).data))
 				#print("\nPrediction:\n" + str(torch.max(output, 1)))
 				print("Corrects:\n" + str(scores))
 	
 	size = len(test_loader.dataset)
 	accuracy = 100 * float(corrects) / size 
 	model.train()
 	return '\nValidation - acc: {:.4f}({}/{}) \n'.format(accuracy, corrects, size), accuracy


def predict(sample_text, model, text_field, label_field, iscuda):

	model.eval()

	text = text_field.preprocess(sample_text)
	text = [[text_field.vocab.stoi[x] for x in text]]
	x = torch.tensor(text)    
	#x = text_field.tensor_type(text)
	x = autograd.Variable(x)
	if iscuda:
		x = x.cuda()
	output = model(x)
	print("Output:"+ str(output))
	msg = ''
	_, predicted = torch.max(output, 0)
	msg += '\nprediction: ' + label_field.vocab.itos[predicted.data[0]+1] + "\n"
	msg += 'probabilities:\n'
	ix = 0
	for v in output:
		label = label_field.vocab.itos[ix+1]
		msg += "\t" + label + " : " + str(v.item()) + "\n"
		ix += 1
	return msg








